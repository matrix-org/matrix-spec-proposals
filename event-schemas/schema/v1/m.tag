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
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      }
    }
  },
 "required": ["type", "content"]
}
