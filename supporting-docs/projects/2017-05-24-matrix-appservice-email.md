---
layout: project
title: Matrix E-mail Bridge
categories: projects as
description: Two ways from/to E-mail bridge
author: Kamax.io, sponsored by Open-Xchange
maturity: Alpha
---

# {{ page.title }}
An application service gateway for bridging between E-mail and Matrix, written using Spring Boot (Java) using [matrix-java-sdk](https://github.com/kamax-io/matrix-java-sdk).  
You can get the [code on github](https://github.com/kamax-io/matrix-appservice-email).

Features:
- Matrix to E-mail forwarding
- E-mail to Matrix forwarding
- E-mail <-> Matrix <-> E-mail forwarding, if several bridge users are present within a room
- Fully configuration notification templates, per event
- Subscription portal where E-mail users can manage their notifications
