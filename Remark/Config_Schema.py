# Description: Config file JSON-schema
# Documentation: command_line.txt

configSchema = {
    "$schema": "http://json-schema.org/draft-04/schema#",

    "type" : "object",
    "properties" : {
        "disable" : {
            "$ref" : "#/definitions/string_set"
        },
        "flags" : {
            "$ref" : "#/definitions/string_set"
        },
        "include" : {
            "$ref" : "#/definitions/string_set"
        },
        "exclude" : {
            "$ref" : "#/definitions/string_set"
        }
    },

    "definitions" : {
        "string_set" : {
            "type" : "array",
            "items" : {
                "type" : "string"
            }
        }
    }
}
