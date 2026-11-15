---
id: deploy-website
type: playbook
title: Déployer le site (Cloudflare Workers)
status: active
project: [website, booking-app]
tags: [deploy, cloudflare]
updated: 2026-11-09
lang: fr
---

## Quand l'utiliser
Pour chaque mise en production du site ou de l'application de réservation.

## Étapes
1. Vérifier le compte propriétaire de la zone ([[L-0001]]).
2. `npm run build` puis `wrangler deploy`.
3. Ouvrir la page d'accueil et le formulaire de contact.

## Retour arrière
`wrangler rollback` vers la version précédente.
