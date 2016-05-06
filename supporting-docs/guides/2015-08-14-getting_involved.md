---
layout: post
title: Getting involved
categories: guides
---

# How can I get involved?
Matrix is an ecosystem consisting of several apps written by lots of people. We at Matrix.org have written one server and a few clients, and people in the community have also written several clients, servers, and Application Services. We are collecting [a list of all known Matrix-apps](https://matrix.org/blog/try-matrix-now/).

|

You have a few options when it comes to getting involved: if you just want to use Matrix, you can [register an account on a public server using a public webclient](#reg). If you have a virtual private server (VPS) or similar, you might want to [run a server and/or client yourself](#run). If you want to look under the hood, you can [checkout the code and modify it - or write your own client or server](#checkout). Or you can write an [Application Service](#as), for example a bridge to an existing ecosystem.

|

We very much welcome [contributions](https://github.com/matrix-org/synapse/blob/master/CONTRIBUTING.rst) to any of our projects, which you can find in our [github space](https://github.com/matrix-org/).

|

<a class="anchor" id="reg"></a>

## Access Matrix via a public webclient/server

The easiest thing to do if you want to just have a play, is to use our reference webclient and create a user on the matrix.org homeserver. You do that by visiting http://matrix.org/beta/, selecting "Create account" and choosing your userID and password on the next page. You can also add your email, but this is optional (adding it will make it easier for your friends to find your Matrix user in the future). 

| 

At the bottom of the account creation page, you can pick the homeserver and identity server you want to use. In this case, we are using matrix.org's homeserver, so just leave it as-is. Your full Matrix-userID will be formed partly from the hostname your server is running as, and partly from an userID you specify when you create the account. For example, if you put bob as your userID, your full Matrix-userID will be @bob:matrix.org ("bob on matrix.org"). 

| 

You can use multiple clients with the same user, so you might want to also look at our [Android](https://github.com/matrix-org/matrix-android-console) or [iOS](https://github.com/matrix-org/matrix-ios-console) clients for your mobile phone!

|

<a class="anchor" id="run"></a>

## Run a server and/or client yourself

You can clone our open source projects and run clients and servers yourself. Here is how:

### Running your own client:

You can run your own Matrix client; there are [numerous clients available](https://matrix.org/blog/try-matrix-now/). You can take Matrix.org's [reference client](https://github.com/matrix-org/matrix-angular-sdk) and use it as-is - or modify it any way you want! Since it's written in JavaScript, running a client is [really easy](https://github.com/matrix-org/matrix-angular-sdk#running)!

|

### Running your own homeserver:

One of the core features of Matrix is that anyone can run a homeserver and join the federated network on equal terms (there is no hierarchy). If you want to set up your own homeserver, please see the relevant docs of the server you want to run. If you want to run Matrix.org's reference homeserver, please consult the [readme of the Synapse project](https://github.com/matrix-org/synapse/blob/master/README.rst).

|

Note that Synapse comes with a bundled Matrix.org webclient - but you can tell it to use your [development checkout snapshot instead](https://github.com/matrix-org/matrix-angular-sdk#matrix-angular-sdk) (or to not run a webclient at all via the "web_client: false" config option).

|

<a class="anchor" id="checkout"></a>

## Checkout our code - or write your own

As described above, you can clone our code and [run a server and/or client yourself](#run). Infact, all the code that we at Matrix.org write is available from [our github](http://github.com/matrix-org) - and other servers and clients may also be open sourced - see [our list of all known Matrix-apps](https://matrix.org/blog/try-matrix-now/).

|

You can also implement your own client or server - after all, Matrix is at its core "just" a specification of a protocol.

|

### Write your own client:

The [client-server API spec](http://matrix.org/docs/howtos/client-server.html) describes what API calls are available to clients, but a quick step-by-step guide would include:

|

1. Get a user either by registering your user in an existing client or running the [new-user script](https://github.com/matrix-org/synapse/blob/master/scripts/register_new_matrix_user) if you are running your own Synapse homeserver.

2. Assuming the homeserver you are using allows logins by password, log in via the login API: 
```
curl -XPOST -d '{"type":"m.login.password", "user":"example", "password":"wordpass"}' "http://localhost:8008/_matrix/client/api/v1/login"
```
3. If successful, this returns the following, including an `access_token`:

        {
            "access_token": "QGV4YW1wbGU6bG9jYWxob3N0.vRDLTgxefmKWQEtgGd",
            "home_server": "localhost",
            "user_id": "@example:localhost"
        }

4. This ``access_token`` will be used for authentication for the rest of your API calls. Potentially the next step you want is to make a call to the initialSync API and get the last x events from each room your user is in (via the limit parameter):
```
curl -XGET "http://localhost:8008/_matrix/client/api/v1/initialSync?limit=1&access_token=YOUR_ACCESS_TOKEN"
```

5. In addition to the last x events for all the rooms the user is interested in, this returns all the presences relevant for these rooms. Once you know which rooms the client has previously interacted with, you need to listen for incoming events. This can be done like so:
```
curl -XGET "http://localhost:8008/_matrix/client/api/v1/events?access_token=YOUR_ACCESS_TOKEN"
```

6. This request will block waiting for an incoming event, timing out after several seconds if there is no event, returning something like this:

        {
            "chunk": [],
            "end": "s39_18_0",
            "start": "s39_18_0"
        }

7. Even if there are no new events (as in the example above), there will be some pagination stream response keys. The client should make subsequent requests using the value of the "end" key (in this case s39_18_0) as the from query parameter e.g.
```
http://localhost:8008/_matrix/client/api/v1/events?access _token=YOUR_ACCESS_TOKEN&from=s39_18_0
```

8. This ensures that you only get new events. Now you have initial rooms and presence, and a stream of events - a good client should be able to process all these events and present them to the user. And potentially you might want to add functionality to generate events as well (such as messages from the user, for example) - again please consult the [client-server API spec](http://matrix.org/docs/howtos/client-server.html)!

| 

### Write your own server:

We are still working on the server-server spec, so the best thing to do if you are interested in writing a server, is to come talk to us in [#matrix:matrix.org](https://matrix.org/beta/#/room/%23matrix:matrix.org).
 
If you are interested in how federation works, please see the [federation API chapter in the spec](http://matrix.org/docs/spec/#federation-api).

|

<a class="anchor" id="as"></a>

## Write an Application Service:

Information about Application services and how they can be used can be found in the [Application services](./application_services.html) document! (This is based on Kegan's excellent blog posts, but now lives here so it can be kept up-to-date!)
