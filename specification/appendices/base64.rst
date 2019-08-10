.. Copyright 2017 Vector Creations Limited
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

Unpadded Base64
---------------

*Unpadded* Base64 refers to 'standard' Base64 encoding as defined in `RFC
4648`_, without "=" padding. Specifically, where RFC 4648 requires that encoded
data be padded to a multiple of four characters using ``=`` characters,
unpadded Base64 omits this padding.

For reference, RFC 4648 uses the following alphabet for Base 64::

     Value Encoding  Value Encoding  Value Encoding  Value Encoding
         0 A            17 R            34 i            51 z
         1 B            18 S            35 j            52 0
         2 C            19 T            36 k            53 1
         3 D            20 U            37 l            54 2
         4 E            21 V            38 m            55 3
         5 F            22 W            39 n            56 4
         6 G            23 X            40 o            57 5
         7 H            24 Y            41 p            58 6
         8 I            25 Z            42 q            59 7
         9 J            26 a            43 r            60 8
        10 K            27 b            44 s            61 9
        11 L            28 c            45 t            62 +
        12 M            29 d            46 u            63 /
        13 N            30 e            47 v
        14 O            31 f            48 w
        15 P            32 g            49 x
        16 Q            33 h            50 y

Examples of strings encoded using unpadded Base64::

   UNPADDED_BASE64("") = ""
   UNPADDED_BASE64("f") = "Zg"
   UNPADDED_BASE64("fo") = "Zm8"
   UNPADDED_BASE64("foo") = "Zm9v"
   UNPADDED_BASE64("foob") = "Zm9vYg"
   UNPADDED_BASE64("fooba") = "Zm9vYmE"
   UNPADDED_BASE64("foobar") = "Zm9vYmFy"

When decoding Base64, implementations SHOULD accept input with or without
padding characters wherever possible, to ensure maximum interoperability.

.. _`RFC 4648`: https://tools.ietf.org/html/rfc4648
