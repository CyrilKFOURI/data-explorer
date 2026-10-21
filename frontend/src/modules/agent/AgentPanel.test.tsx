import { fireEvent, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { column, roles } from "../../test/columns";
import { dataset, health, mockApi } from "../../test/mockApi";
import { renderAt } from "../../test/render";

const settings = (configured: boolean) => ({
  provider: "anthropic",
  model: "claude-opus-5-5",
  models: ["claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"],
  effort: "high",
  budget_usd: 1,
  key: { configured, source: configured ? "file" : "none", hint: configured ? "…abcd" : null },
  sdk_installed: true,
});

const conversation = {
  id: "c1",
  dataset_id: "d1",
  title: "New conversation",
  model: "claude-opus-5-5",
  cost_usd: 0,
  created_at: "2026-10-21T10:00:00Z",
  updated_at: "2026-10-21T10:00:00Z",
  running: false,
};

const turn = [
  { type: "spent", turn_usd: 0.01, conversation_usd: 0.01, tokens: 900 },
  { type: "step_started", id: "s1", tool: "rank_associations_with", label: "Ranking what is linked to Survived", input: {} },
  {
    type: "step_done",
    id: "s1",
    ok: true,
    summary: "Strongest link with Survived: Sex (Cramér's V 0.54)",
    link: { page: "correlations", params: {}, label: "Open the correlations" },
    ms: 420,
  },
  { type: "text", text: "**Sex** is the strongest driver." },
  { type: "done", end: "answered", message: null, turn_usd: 0.02, conversation_usd: 0.02 },
];

const saved = [
  { role: "user", text: "What is most linked to Survived, and how?", thinking: "", steps: [] },
  {
    role: "assistant",
    text: "**Sex** is the strongest driver.",
    thinking: "",
    steps: [
      {
        id: "s1",
        tool: "rank_associations_with",
        label: "Ranking what is linked to Survived",
        input: {},
        ok: true,
        summary: "Strongest link with Survived: Sex (Cramér's V 0.54)",
        link: { page: "correlations", params: {}, label: "Open the correlations" },
      },
    ],
  },
];

function setup(configured = true) {
  let answered = false;
  const calls = mockApi({
    "GET /health": health,
    "GET /datasets/d1": dataset({ types_reviewed_at: "2026-10-13T10:00:00Z" }),
    "POST /datasets/d1/open": dataset(),
    "GET /datasets/d1/columns": [
      column({ name: "Survived", type: "boolean", detected_type: "boolean" }),
      column({ name: "Age", position: 1 }),
    ],
    "GET /column-roles": roles,
    "GET /modules/agent/settings": settings(configured),
    "GET /modules/agent/datasets/d1/conversations": [],
    "POST /modules/agent/datasets/d1/conversations": conversation,
    "GET /modules/agent/conversations/c1": () => ({ conversation, messages: answered ? saved : [] }),
  });
  const json = globalThis.fetch;
  vi.stubGlobal("fetch", async (input: RequestInfo | URL, init?: RequestInit) => {
    if (String(input).endsWith("/conversations/c1/messages")) {
      calls.push({ key: "POST /modules/agent/conversations/c1/messages", body: JSON.parse(String(init?.body)), params: new URLSearchParams() });
      answered = true;
      const body = turn.map((event) => `data: ${JSON.stringify(event)}\n\n`).join("");
      return new Response(body, { headers: { "Content-Type": "text/event-stream" } });
    }
    return json(input, init);
  });
  return calls;
}

beforeEach(() => localStorage.clear());
afterEach(() => vi.unstubAllGlobals());

describe("Assistant panel", () => {
  it("asks a suggested question, shows the analysis it ran and the answer", async () => {
    const calls = setup();
    renderAt("/d/d1/columns");

    fireEvent.click(await screen.findByRole("button", { name: "Ask the assistant" }));
    const panel = await screen.findByRole("complementary", { name: "Assistant" });
    fireEvent.click(await within(panel).findByRole("button", { name: "What is most linked to Survived, and how?" }));

    expect(await within(panel).findByText("Sex")).toBeInTheDocument();
    expect(within(panel).getByText("Ranking what is linked to Survived")).toBeInTheDocument();
    expect(within(panel).getByRole("link", { name: /Open the correlations/ })).toHaveAttribute("href", "/d/d1/correlations");
    const sent = calls.find((c) => c.key === "POST /modules/agent/conversations/c1/messages");
    expect(sent?.body).toMatchObject({ text: "What is most linked to Survived, and how?", filters: [], page: "Columns" });
    expect(localStorage.getItem("de.agent.open")).toBe("true");
  });

  it("explains how to add a key when none is set", async () => {
    setup(false);
    renderAt("/d/d1/columns");
    await screen.findByRole("button", { name: "Ask the assistant" });

    fireEvent.keyDown(window, { key: "j", ctrlKey: true });
    const panel = await screen.findByRole("complementary", { name: "Assistant" });

    expect(await within(panel).findByText("Set up the assistant")).toBeInTheDocument();
    expect(within(panel).getByRole("textbox", { name: "Message to the assistant" })).toBeDisabled();
    fireEvent.click(within(panel).getByRole("button", { name: "Add an API key" }));
    expect(await within(panel).findByLabelText("Anthropic API key")).toBeInTheDocument();
  });

  it("stays out of the way outside a dataset", async () => {
    mockApi({ "GET /health": health, "GET /datasets": [], "GET /samples": [] });
    renderAt("/");

    await screen.findAllByRole("heading");
    expect(screen.queryByRole("button", { name: "Ask the assistant" })).not.toBeInTheDocument();
  });
});

describe("Assistant confirmations", () => {
  it("asks before a change and sends the user's answer", async () => {
    const calls = setup();
    let push: ((event: object) => void) | null = null;
    let close: () => void = () => {};
    const json = globalThis.fetch;
    vi.stubGlobal("fetch", async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/conversations/c1/messages")) {
        const encoder = new TextEncoder();
        const body = new ReadableStream({
          start(controller) {
            push = (event) => controller.enqueue(encoder.encode(`data: ${JSON.stringify(event)}\n\n`));
            close = () => controller.close();
          },
        });
        return new Response(body, { headers: { "Content-Type": "text/event-stream" } });
      }
      if (url.endsWith("/conversations/c1/confirm/s1")) {
        calls.push({ key: "POST confirm", body: JSON.parse(String(init?.body)), params: new URLSearchParams() });
        return new Response(null, { status: 204 });
      }
      return json(input, init);
    });
    renderAt("/d/d1/columns");
    fireEvent.click(await screen.findByRole("button", { name: "Ask the assistant" }));
    const panel = await screen.findByRole("complementary", { name: "Assistant" });
    fireEvent.change(await within(panel).findByRole("textbox", { name: "Message to the assistant" }), {
      target: { value: "Save a revenue KPI" },
    });
    fireEvent.click(within(panel).getByRole("button", { name: "Send" }));

    await vi.waitFor(() => expect(push).not.toBeNull());
    const send = (event: object) => push?.(event);
    send({ type: "step_started", id: "s1", tool: "save_kpi", label: "Saving the KPI", input: {} });
    send({ type: "confirm", id: "s1", tool: "save_kpi", text: "Save the KPI “Revenue” in the KPI builder." });

    const card = await within(panel).findByRole("group", { name: "The assistant asks before changing something" });
    expect(within(card).getByText("Save the KPI “Revenue” in the KPI builder.")).toBeInTheDocument();
    fireEvent.click(within(card).getByRole("button", { name: "Confirm" }));

    await vi.waitFor(() => expect(calls.find((c) => c.key === "POST confirm")?.body).toEqual({ approved: true }));
    send({ type: "done", end: "answered", message: null, turn_usd: 0.01, conversation_usd: 0.01 });
    close();
  });
});
