---
id: datenbank-backup
type: playbook
title: Tägliches Datenbank-Backup prüfen
status: active
project: [booking-app]
tags: [backup, postgres]
updated: 2026-11-13
lang: de
---

## Wann verwenden
Jeden Montag, und vor jeder größeren Änderung an der Buchungs-App.

## Schritte
1. Letztes Backup in den Speicher-Bucket herunterladen.
2. In eine leere Datenbank einspielen und die Anzahl der Mitglieder vergleichen.

## Prüfen
Die Zahlen stimmen mit der Produktion überein. Siehe auch [[L-0003]].
