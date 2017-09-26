---
layout: project
title: tiny-matrix-bot
categories: projects other
description: Bot with plugins
author: Ander Punnar
maturity: Alpha
---

# {{ page.title }}
Simple and dirty matrix.org bot based on matrix-python-sdk

<del>no manual</del>, no support, no warranty

pull requests are welcome!

manual:

* git clone https://github.com/4nd3r/tiny-matrix-bot
* git clone https://github.com/matrix-org/matrix-python-sdk
* cd tiny-matrix-bot
* ln -s ../matrix-python-sdk/matrix_client
* cp tiny-matrix-bot.cfg.sample tiny-matrix-bot.cfg
* vim tiny-matrix-bot.cfg
* screen ./tiny-matrix-bot.py tiny-matrix-bot.cfg
* scripts must have execute bit - chmod +x

|

Follow the progress and grab the code from [GitHub](https://github.com/4nd3r/tiny-matrix-bot/)!
