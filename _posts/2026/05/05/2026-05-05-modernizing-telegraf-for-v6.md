---
layout: post
title: 'Modernizing Telegraf for v6'
author: Leask
date: '2026-05-05 19:02:00 -0400'
categories:
- Computers and Internet
---

[Telegraf](https://github.com/telegraf/telegraf) is one of the important
community projects in the Telegram bot ecosystem. It has been around for years,
it has a clean programming model, and many Node.js bots still depend on it.

But the Telegram platform has not stood still. The official
[Bot API](https://core.telegram.org/bots/api) has kept moving, while Telegraf's
mainline updates have slowed down. That gap matters more now than it did a few
years ago. Telegram is no longer only a place for simple command bots. It is
increasingly a practical interface for AI agents: private chats, group
coordination, media input, inline workflows, web app handoffs, notifications,
and long-running assistant loops.

If a framework does not keep up with the upstream API, every serious bot starts
paying the tax locally. Developers patch missing methods, copy new Telegram
types into application code, work around outdated examples, or avoid newer
features entirely. That is not a good base for agent systems, and it is not a
good outcome for a project as widely used as Telegraf.

So I forked the project and started a larger modernization pass toward v6. The
main pull request is
[telegraf/telegraf#2092](https://github.com/telegraf/telegraf/pull/2092). The
companion type-definition work is
[telegraf/types#14](https://github.com/telegraf/types/pull/14). The docs
follow-up is
[feathers-studio/telegraf-docs#23](https://github.com/feathers-studio/telegraf-docs/pull/23).

## What v6 is trying to do

This is not a rewrite for the sake of rewriting. Telegraf's existing model is
still good: middleware, context helpers, Composer routing, scenes, sessions,
and the low-friction `bot.command` / `bot.on` style are all worth preserving.

The goal of v6 is to make that model current again:

- align Telegraf with Telegram Bot API 9.6;
- expose runtime wrappers for the official API surface;
- use `@telegraf/types` as the source of truth for future Bot API syncs;
- modernize the runtime baseline around Node.js 20 and native platform APIs;
- remove stale compatibility assumptions that made the networking layer harder
  to maintain;
- add tests that make future API drift visible instead of silent.

The most important design choice is to keep future Bot API updates mechanical.
The type package should describe Telegram's canonical API. Telegraf should then
wrap every typed method it can support, and tests should fail when the runtime
falls behind the declarations. That turns "someone should check the changelog"
into a concrete maintenance workflow.

## Catching up with the Bot API

The v6 branch updates Telegraf for the current Bot API generation and adds
coverage around the newly typed surface. The tests now inspect
`@telegraf/types` and verify that `Telegram` has wrappers for the official
methods. This is a small but useful guardrail: once the type package moves, the
runtime can no longer quietly miss a method.

Newer request shapes also exposed a multipart edge case. Some Bot API payloads
can contain nested `InputFile` values, so the upload serializer now handles
those recursively. That is the kind of detail that tends to break only after a
real bot starts using a new Telegram feature. It is better to cover it in the
framework.

The types work is currently staged through the companion PR. Until it lands
upstream or is published as an official package, the Telegraf PR temporarily
points at my `@telegraf/types` fork. That is not the final desired dependency;
it is only a way to validate the runtime against the actual Bot API 9.6 shape
while the upstream review is happening.

## Modern Node, less baggage

The networking layer changed more than I first expected. Older Telegraf releases
depended on `node-fetch` and exposed `node-fetch`-specific agent options such
as `telegram.agent` and `telegram.attachmentAgent`. That made sense in older
Node versions, but it is no longer the right default for a modern Node.js
runtime.

Telegraf v6 uses the native `globalThis.fetch` by default. It no longer bundles
`node-fetch`, and the old agent hooks are replaced by a more general extension
point: inject your own `telegram.fetch`.

For example, a proxy setup becomes:

```ts
import { Telegraf } from 'telegraf';
import fetch from 'node-fetch';
import { HttpsProxyAgent } from 'https-proxy-agent';

const agent = new HttpsProxyAgent(process.env.HTTPS_PROXY);
const fetchWithProxy = (url: URL | string, init?: RequestInit) =>
    fetch(
        String(url),
        { ...init, agent } as unknown as Parameters<typeof fetch>[1],
    );

const bot = new Telegraf(process.env.BOT_TOKEN, {
    telegram: { fetch: fetchWithProxy },
});
```

The important part is not `node-fetch`. Users can bring any fetch-compatible
implementation they need for proxies, custom TLS, compression, logging, or
special deployment environments. Telegraf just needs one clean hook, and that
same hook is used for both Bot API calls and URL attachments.

The Node.js baseline also moved to Node 20. That allowed the codebase to remove
older runtime shims and update supporting tools such as the timeout path, lint
configuration, tests, and release workflow. A major version is the right place
to do that. Keeping a modern framework tied to old platform assumptions makes
every future change more expensive.

## Tests as a maintenance contract

The branch is not only a pile of wrappers. I spent a lot of time making the
tests describe the intended maintenance contract:

- Bot API methods declared by `@telegraf/types` must be represented at runtime;
- newer Bot API fields should be visible in the generated type surface;
- custom fetch must work for normal API calls;
- custom fetch must also work for URL attachments;
- request timeout behavior must abort fetch calls cleanly;
- multipart form data must preserve nested `InputFile` payloads;
- webhook rejection behavior must return useful HTTP status codes and headers.

The current Telegraf test suite passes with 180 tests. The package also builds,
lints, generates TypeDoc output, and passes an npm pack dry run. There are still
TypeDoc warnings, but they are warnings in the generated reference surface, not
failing runtime behavior.

## The documentation had to move too

Modernizing the code without updating the docs would leave users with the old
mental model. That is why I also opened a documentation PR against
[feathers-studio/telegraf-docs](https://github.com/feathers-studio/telegraf-docs).

The docs update does a few practical things:

- explains the new native `globalThis.fetch` default;
- replaces old proxy examples based on `telegram.agent` with `telegram.fetch`;
- updates the context options shape to include `fetch` and `requestTimeout`;
- refreshes examples that were stale against newer Bot API typings, such as
  `thumbnail_url`, `correct_option_ids`, and `telegraf/types` imports;
- fixes framework-specific webhook examples for Fastify and Koa;
- moves the AWS Lambda example to the Node.js 20 runtime.

I did not open a separate PR against the upstream `gh-pages` branch. That branch
contains generated TypeDoc output for the published site. The right path is to
land the source changes, then let the release workflow regenerate the site from
the upstream repository when v6 is tagged. Manually editing generated HTML would
create a large diff with very little review value.

## Why this matters now

Telegram is a surprisingly good surface for AI systems. It already has identity,
contacts, groups, rich media, push notifications, inline interactions, and
mobile clients that people actually use. For agents, that makes Telegram a
natural place to receive instructions, ask follow-up questions, send files, and
coordinate with humans.

But agent-facing infrastructure needs boring reliability. Missing API coverage,
stale types, and outdated networking assumptions are exactly the small cracks
that become annoying in production. A framework like Telegraf should make the
common path simple while still giving advanced users room to customize the edge
cases.

That is the v6 direction: keep the Telegraf programming model, catch up with
Telegram's official API, modernize the runtime, and make future API updates
less heroic.

## Current status

At the time of writing:

- the main Telegraf v6 PR is open as
  [telegraf/telegraf#2092](https://github.com/telegraf/telegraf/pull/2092);
- the Bot API 9.6 types PR is open as
  [telegraf/types#14](https://github.com/telegraf/types/pull/14);
- the documentation PR is ready for review as
  [feathers-studio/telegraf-docs#23](https://github.com/feathers-studio/telegraf-docs/pull/23).

The work is intentionally staged. First the official type surface needs to be
accepted or published. Then the main Telegraf dependency can switch back from
the temporary fork to the official `@telegraf/types` release. After that, the
docs can point at the published `telegraf@^6.0.0` package instead of the stacked
branch.

That is a bit of coordination, but it is the kind that makes an open source
upgrade reviewable. Types, runtime, tests, release notes, and examples each
have their own place, and the final result should be a Telegraf line that is
much easier to keep current with Telegram from here.
