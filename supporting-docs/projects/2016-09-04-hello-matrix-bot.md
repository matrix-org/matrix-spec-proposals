---
layout: project
title: Hello Matrix Bot
categories: projects other
description: Bot with an array of plugins
author: Alexander Rudyk
maturity: Alpha
---

# {{ page.title }}
This project is a simple attempt at providing a friendly face to as many popular services as possible, making them accessible from any Matrixroom. "Hello Matrix" is written as NodeJS application, building on matrix-js-sdk, the JavaScript SDK from the creators of Matrix. It is a hobby project and as such far from feature complete, in fact it is all very basic right now - hopefully this will change over the coming months.

You can either use the "Hello Matrix" bot running on our server (just invite @hello-matrix:matrix.org into your Matrix room) or you can check out the code from this repository and run your own instance of "Hello Matrix" (also providing your own API keys to the services you want to use).

"Hello Matrix" currently supports the following services:

* Sending and receiving messages using Bitmessage
* Numeric calculations using Wolfram Alpha
* Throwing the dice (generating a random number)
* Adding tasks to your Kanban board from Kanban Tool and getting notified of task status changes
* Tracerouting a given IP
* Weather from OpenWeatherMap
* Providing WHOIS information on a domain or IP address
* Adding tasks and monitoring progress on Wunderlist lists
* The goal is to add at least generic web hook functionality in the coming months, which would immediately make a large number of other integrations possible. We’ll keep you updated on any progress.

|

Follow the progress and grab the code from [gitlab](https://gitlab.com/argit/hello-matrix-bot)!
