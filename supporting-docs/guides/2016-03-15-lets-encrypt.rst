---
layout: post
title: Let's Encrypt Matrix
categories: guides
---

====================
Let's Encrypt Matrix
====================

Let's Encrypt is a free Certificate Authority that makes it easy to secure your server's internet traffic. This makes it really easy to secure your Matrix homeserver, and this guide will explain exactly how you do this. Guide written by William A Stevens - thanks!

0: Prerequisites
================
* Install Synapse_.
* Install (or Download) `Let's Encrypt`_

1: Get certificates
===================
When executing the Let's Encrypt client, it will ask for the domain name of your server, and your email address. The domain list can include multiple names and should include any domain you want to access the server from.

Also, the certificates will be in a folder under /etc/letsencrypt (see below) and owned by root. These files should be copied to the same directory as the synapse install and owned by the user synapse is run as.

::

# cd (path to synapse)
# ./letsencrypt-auto certonly --standalone
# sudo cp /etc/letsencrypt/live/(your domain name)/* .
# sudo chown (user synapse runs as) *.pem

A note about renewal
--------------------
These certificates will expire in 3 months. To renew certificates, just repeat this step.

2: Install Certificates
=======================
At the top of your homeserver.yaml there should be two keys, ```tls_certificate_path``` and ```tls_private_key_path```. These should be changed so that instead of pointing to the default keys, they now point to the Let's Encrypt keys. ```tls_certificate_path``` should point to the ```fullchain.pem``` in the synapse install directory. ```tls_private_key_path``` should point to the ```privkey.pem``` in the synapse install directory. ```tls_dh_params_path``` can stay the same as before.

.. _Synapse: https://github.com/matrix-org/synapse/blob/master/README.rst#synapse-installation
.. _Let's Encrypt: https://letsencrypt.readthedocs.org/en/latest/using.html#installation
