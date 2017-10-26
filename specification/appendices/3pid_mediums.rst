.. Copyright 2017 Kamax.io
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..     http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.

3PID Medium types
-----------------
3PID medium types are identifiers refering to other networks can connect to.
They are always lowercase.

The following list are the official identifiers for most used networks:

========== ==================
Medium ID  Network
========== ==================
``email``  E-mail
``msisdn`` PSTN Phone numbers
========== ==================

This list is not exhaustive and arbitrary values can be used throughout the protocol.

| In case a server is not capable of handing a request due to a 3PID medium type, like
  sending a notification, it should return a 501 HTTP Status code (Not Implemented).  
| The status code can be overwritten at the endpoint specification level.
