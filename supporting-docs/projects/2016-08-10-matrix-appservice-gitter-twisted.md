---
layout: project
title: matrix-appservice-gitter-twisted
categories: projects as
author: Remi Rampin
maturity: Alpha
---

# {{ page.title }}
This is a Python 2 application using Twisted that bridges the Matrix chat network with the Gitter system.

This is supposed to be deployed as a Matrix application service alongside a homeserver. It allows users to log in to their personal Gitter accounts and chat in Gitter rooms via their Matrix client.

Contrary to other bridges, this doesn't link a public Matrix room with a Gitter one. You won't be able to join a Gitter room without a Gitter account. On the other hand, Gitter users won't see the difference between a Matrix user and a normal Gitter user, since they will appear to be chatting natively.

Find it on [GitHub](https://github.com/remram44/matrix-appservice-gitter-twisted/).
