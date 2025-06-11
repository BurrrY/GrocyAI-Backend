from my_grocy import get_amount_per_name, consumer_amount_per_name, add_amount_per_name, set_amount_per_name, \
    get_shoppinglist, stock_shoppinglist_addProduct, stock_shoppinglist_removeProduct

tools = [


    {
        "type": "function",
        "function": {
        "name": "stock_shoppinglist_remove-product",
        "description": "remove a product from the shoppinglist with given amount",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "Name of the Product"
                },
                "amount": {
                    "type": "string",
                    "description": "number of items of the product to be removed from the shopping list"
                }
            },
            "required": ["product_name", "amount"]
        }
        }
    },


    {
        "type": "function",
        "function": {
            "name": "get_shoppinglist",
            "description": "get a list of all products which are currently on the shoppinglist",
        }
    },


    {
        "type": "function",
        "function": {
            "name": "stock_shoppinglist_add-product",
            "description": "add a product to the shoppinglist",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Name of the Product"
                    },
                    "amount": {
                        "type": "string",
                        "description": "number of items of the product to be added to the shopping list"
                    }
                },
                "required": ["product_name", "amount"]
            }
        }
    },


    {
        "type": "function",
        "function": {
        "name": "get_amount_per_name",
        "description": "get the available amount of a product from grocy.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "Name of the Product"
                }
            },
            "required": ["product_name"]
        }
        }
    },

    {
        "type": "function",
        "function": {
        "name": "consumer_amount_per_name",
        "description": "eat, remove, consume or use a certain amount of a product",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "Name of the Product"
                },
                "amount": {
                    "type": "string",
                    "description": "Consumed amount of the product"
                }
            },
            "required": ["product_name", "amount"]
        }
        }
    },

    {
        "type": "function",
        "function": {
        "name": "set_amount_per_name",
        "description": "set the total amount of a product in stock",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "Name of the Product"
                },
                "amount": {
                    "type": "string",
                    "description": "new amount of the product"
                }
            },
            "required": ["product_name", "amount"]
        }
        }
    },

    {
        "type": "function",
        "function": {
        "name": "add_amount_per_name",
        "description": "purchase or added a certain amount of a product to the stock",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "Name of the Product"
                },
                "amount": {
                    "type": "string",
                    "description": "additional amount of the product"
                }
            },
            "required": ["product_name", "amount"]
        }
        }
    }
]
function_map = {
    "stock_shoppinglist_remove-product": stock_shoppinglist_removeProduct,
    "stock_shoppinglist_add-product": stock_shoppinglist_addProduct,
    "get_shoppinglist": get_shoppinglist,
    "get_amount_per_name": get_amount_per_name,
    "consumer_amount_per_name": consumer_amount_per_name,
    "add_amount_per_name": add_amount_per_name,
    "set_amount_per_name": set_amount_per_name
}
