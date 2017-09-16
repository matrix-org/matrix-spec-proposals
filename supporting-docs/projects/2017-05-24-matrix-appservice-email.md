---
layout: project
title: Matrix Email Bridge
categories: projects as
description: Two ways Email<->Matrix bridge
author: Kamax.io and Open-Xchange
maturity: Alpha
---

# {{ page.title }}
An application service gateway for bridging between Email and Matrix, written using Spring Boot (Java) using [matrix-java-sdk](https://github.com/kamax-io/matrix-java-sdk).  
You can get the [code on github](https://github.com/kamax-io/matrix-appservice-email).

Features:
 - Matrix to Email forwarding
 - Email to Matrix forwarding
 - Email <-> Matrix <-> Email forwarding, if several bridge users are present within a room
 - Fully configuration notification templates, per event
 - Subscription portal where E-mail users can manage their notifications
