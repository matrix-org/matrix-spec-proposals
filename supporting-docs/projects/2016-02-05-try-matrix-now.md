---
layout: project
title: Try Matrix Now!
categories: projects
---

<div class='font18'>
Matrix is a whole ecosystem of matrix-enabled clients, servers, gateways, application services, bots, etc.
</div>

|

<div class='font18 bold'>
The easiest way to get started is to pick a client that appeals and join #matrix:matrix.org:
</div>

<p>&nbsp;</p>

<table class='bigtable'>
  <tr>
    <td class='bigproject'>
      <a href='./client/weechat.html' class='font18 bold'>
        Weechat/Matrix
      </a><br />
      If you like command line clients, try the Weechat plugin.<br /><br />
      <a href='./client/weechat.html'>
        <img src='https://matrix.org/blog/wp-content/uploads/2015/04/Screen-Shot-2015-08-07-at-13.31.29-300x209.png' class='featured_screenshot'>
      </a>
    </td>
    <td class='bigproject'>
      <a href='./client/riot.html' class='font18 bold'>
        Riot
      </a><br />
      If you like glossy and feature-rich web clients, try Riot.<br /><br />
      <a href='./client/riot.html'>
        <img src='/docs/projects/images/riot-web-featured.png' class='featured_screenshot'>
      </a>
    </td>
    <td class='bigproject'>
      <a href='./client/riot-ios.html' class='font18 bold'>
        Riot iOS
      </a><br />
      You can also access Matrix on your iOS phone via Riot iOS.<br /><br />
      <a href='./client/riot-ios.html'>
        <img src='/docs/projects/images/vector-iOS-featured.png' class='featured_screenshot'>
      </a>
    </td>
    <td class='bigproject'>
      <a href='./client/riot-android.html' class='font18 bold'>
        Riot Android
      </a><br />
      Riot is also available on Android devices!<br /><br />
      <a href='./client/riot-android.html'>
        <img src='/docs/projects/images/vector-android-featured.png' class='featured_screenshot'>
      </a>
    </td>
  </tr>
</table>


This page aims to collect all known Matrix projects - if you want to add a new one (or update an existing one), you can submit a PR to the [matrix-doc](https://github.com/matrix-org/matrix-doc) project on github - the existing projects can be found [here](https://github.com/matrix-org/matrix-doc/tree/master/supporting-docs/projects) - or just let us know in the #matrix:matrix.org room.

| 

<div class='font18'>
Projects using Matrix:
</div>

* TOC
{:toc .toc}

|

Clients
=======

<table>
  {% assign post_nr = '0' %}
  {% for post in site.categories.client reversed limit:100 %}
    {% assign add_new_row_test = post_nr | modulo:6 %}
    {% if add_new_row_test == 0 %}<tr>{% endif %}
      <td class='project'>
        <a href='/docs{{ BASE_PATH }}{{ post.url }}'> 
          <img class='thumbnail' src='{{ post.thumbnail }}'>
        </a>
        <br />
        <a href='/docs{{ BASE_PATH }}{{ post.url }}'>  
          {{ post.title }}
        </a><br />
        <div style='margin-bottom: 8px;'>
          {{ post.description }}
        </div> 
        Author: {{ post.author }}<br />
        Maturity: {{ post.maturity }} 
      </td>
      {% assign post_nr = post_nr | plus: '1' %}
      {% assign add_new_row_test = post_nr | modulo:6 %}
    {% if add_new_row_test == 0 %}</tr>{% endif %}
  {% endfor %}  

 </tr>
</table>

|

Servers
=======

<table>
  {% assign post_nr = '0' %}
  {% for post in site.categories.server reversed limit:100 %}
    {% assign add_new_row_test = post_nr | modulo:6 %}
    {% if add_new_row_test == 0 %}<tr>{% endif %}
      <td class='project'>
        <a href='/docs{{ BASE_PATH }}{{ post.url }}'>
          {{ post.title }}
        </a><br />
        <div style='margin-bottom: 8px;'>
          {{ post.description }}
        </div>
        Author: {{ post.author }}<br />
        Maturity: {{ post.maturity }}
      </td>
      {% assign post_nr = post_nr | plus: '1' %}
      {% assign add_new_row_test = post_nr | modulo:6 %}
    {% if add_new_row_test == 0 %}</tr>{% endif %}
  {% endfor %}

 </tr>
</table>


|

Application Services
====================

<table>
  {% assign post_nr = '0' %}
  {% for post in site.categories.as reversed limit:100 %}
    {% assign add_new_row_test = post_nr | modulo:6 %}
    {% if add_new_row_test == 0 %}<tr>{% endif %}
      <td class='project'>
        <a href='/docs{{ BASE_PATH }}{{ post.url }}'>
          {{ post.title }}
        </a><br />
        <div style='margin-bottom: 8px;'>
          {{ post.description }}
        </div>
        Author: {{ post.author }}<br />
        Maturity: {{ post.maturity }}
      </td>
      {% assign post_nr = post_nr | plus: '1' %}
      {% assign add_new_row_test = post_nr | modulo:6 %}
    {% if add_new_row_test == 0 %}</tr>{% endif %}
  {% endfor %}

 </tr>
</table>

|

Client SDKs
===========

<table>
  {% assign post_nr = '0' %}
  {% for post in site.categories.sdk reversed limit:100 %}
    {% assign add_new_row_test = post_nr | modulo:6 %}
    {% if add_new_row_test == 0 %}<tr>{% endif %}
      <td class='project'>
        <a href='/docs{{ BASE_PATH }}{{ post.url }}'>
          {{ post.title }}
        </a><br />
        <div style='margin-bottom: 8px;'>
          {{ post.description }}
        </div>
        Author: {{ post.author }}<br />
        Maturity: {{ post.maturity }}
      </td>
      {% assign post_nr = post_nr | plus: '1' %}
      {% assign add_new_row_test = post_nr | modulo:6 %}
    {% if add_new_row_test == 0 %}</tr>{% endif %}
  {% endfor %}

 </tr>
</table>

|

Other
=====

<table>
  {% assign post_nr = '0' %}
  {% for post in site.categories.other reversed limit:100 %}
    {% assign add_new_row_test = post_nr | modulo:6 %}
    {% if add_new_row_test == 0 %}<tr>{% endif %}
      <td class='project'>
        <a href='/docs{{ BASE_PATH }}{{ post.url }}'>
          {{ post.title }}
        </a><br />
        <div style='margin-bottom: 8px;'>
          {{ post.description }}
        </div>
        Author: {{ post.author }}<br />
        Maturity: {{ post.maturity }}
      </td>
      {% assign post_nr = post_nr | plus: '1' %}
      {% assign add_new_row_test = post_nr | modulo:6 %}
    {% if add_new_row_test == 0 %}</tr>{% endif %}
  {% endfor %}

 </tr>
</table>

