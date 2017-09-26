---
layout: project
title: Matrix Recorder
categories: projects other
description: Enables you to keep a record of all messages you have received.
author: ar
maturity: Alpha
---

# {{ page.title }}

While Matrix homeservers store your message history so that you can retrieve them on all your devices, currently there is no easy way to download and backup this message history. This is especially relevant for end-to-end (E2E) encrypted rooms because their history cannot be decrypted anymore if you lose your encryption keys (which is as easy as logging out of your Riot client).

This is where Matrix Recorder jumps in. This tool (written in Node.js) retrieves all messages you receive or send just as a regular client would. It uses your existing Matrix account but registers as a new device with its own encryption keys, which means that it can decrypt messages sent to you after Matrix Recorder has been registered. You don’t need to keep it running all the time but can just start it from time to time - it will continue from where it left off when you start it the next time.

All timeline events retrieved that way will be stored in an sqlite database which you can just keep as a backup or use to create your own archive. Matrix Recorder comes with a small utility that extracts messages from this database into HTML files that can be viewed in your browser.

Follow the progress and grab the code from [GitLab](https://gitlab.com/argit/matrix-recorder).
