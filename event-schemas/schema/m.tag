{
  "type": "object",
  "title": "Tag Event",
  "description": "Informs the client of tags on a room.",
  "properties": {
    "type": {
      "type": "string",
      "enum": ["m.tag"]
    },
    "content": {
      "type": "object",
      "properties": {
        "tags": {
          "type": "object",
          "description": "The tags on the room and their contents.",
          "additionalProperties": {
            "title": "Tag",
            "type": "object"
          }
        }
      }
    }
  },
  "required": ["type", "content"]
}
