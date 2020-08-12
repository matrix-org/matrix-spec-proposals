#!/usr/bin/env python3
#
# i18n.py: Generate and merge the i18n files for the spec.

import json
import sys
import os
import os.path

scripts_dir = os.path.dirname(os.path.abspath(__file__))
data_defs_dir = os.path.join(scripts_dir, "../data-definitions")

def merge_sas_emoji_v1():
    emoji = dict() # will be populated by a read
    with open(os.path.join(data_defs_dir, "sas-emoji.json"), encoding="utf8") as f:
        emoji = json.load(f)
        for e in emoji:
            e["translated_descriptions"] = dict()
        pth = os.path.join(data_defs_dir, "sas-emoji-v1-i18n")
        translations = [t for t in os.listdir(pth) if os.path.isfile(os.path.join(pth, t))]
        for translation in translations:
            if translation == "base.json":
                continue
            lang = translation[:-5] # trim off the json extension
            with open(os.path.join(pth, translation), encoding="utf8") as lf:
                descs = json.load(lf)
                for e in emoji:
                    e["translated_descriptions"][lang] = descs[e["description"]]
    with open(os.path.join(data_defs_dir, "sas-emoji.json"), mode="w+", encoding="utf8") as o:
        json.dump(emoji, o, ensure_ascii=False, indent=4)

merge_sas_emoji_v1()
