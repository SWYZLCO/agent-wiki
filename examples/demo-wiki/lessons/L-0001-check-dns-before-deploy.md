---
id: L-0001
type: lesson
title: Check which account owns the DNS zone before deploying
status: active
project: [website]
tags: [cloudflare, dns, deploy]
updated: 2026-10-20
lang: en
---

## What happened
A deployment went to the wrong Cloudflare account because the zone had been added twice.

## Lesson (what to do next time)
Run a WHOIS / nameserver lookup first and confirm the account that owns the zone.

## Evidence
Deployment log of 2026-10-20.
