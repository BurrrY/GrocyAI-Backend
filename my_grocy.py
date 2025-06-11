import logging
import math

from pygrocy2 import Grocy
from pygrocy2.data_models.product import Product
from rapidfuzz import process
import os

from rapidfuzz import fuzz

grocy = Grocy(os.environ.get("GROCY_API_URL"), os.environ.get("GROCY_API_KEY"), port = int(os.environ.get("GROCY_API_PORT")))

def combined_score(c_query: str, target: str, *, score_cutoff=None, **kwargs) -> float:
    return (
        0.5 * fuzz.ratio(c_query, target) +
        0.3 * fuzz.partial_ratio(c_query, target) +
        0.2 * fuzz.token_sort_ratio(c_query, target)
    )

logger = None
def set_logger(theLogger):
    global logger
    logger = theLogger


def set_amount_per_name(product_name, amount):
    found_product = get_prod_from_stock(product_name)
    logger.debug("Found Product: ", str(found_product))

    if isinstance(found_product, Product):
        logger.debug(found_product)
        grocy.inventory_product(new_amount=amount, product_id=found_product.id)
        return {
            "name": found_product.name,
            "old_amount": found_product.available_amount,
            "new_amount": amount,
            "unit_singular": found_product.default_quantity_unit_purchase.name,
            "unit_plural": found_product.default_quantity_unit_purchase.name_plural,
        }
    else:
        return {
            "error": "Product not found",
        }

def add_amount_per_name(product_name, amount):
    found_product = get_prod_from_stock(product_name)
    logger.debug("Found Product: ", str(found_product))

    if isinstance(found_product, Product):
        logger.debug(found_product)
        grocy.add_product(amount=amount, product_id=found_product.id, price=0)
        return {
            "name": found_product.name,
            "new_amount": found_product.available_amount+float(amount),
            "added_amount": amount,
            "unit_singular": found_product.default_quantity_unit_purchase.name,
            "unit_plural": found_product.default_quantity_unit_purchase.name_plural,
        }
    else:
        return {
            "error": "Product not found",
        }

def get_prod_from_stock(product_name):
    logger.debug("Searching for ", product_name)

    found_product = None
    all_products=[]
    try:
        all_products = grocy.all_products()
    except Exception as e:
        logger.debug(e)

    name_map = {p.name: p for p in all_products}

    best_match = process.extractOne(
        product_name,
        name_map.keys(),
        scorer=combined_score,
    )
    logger.debug("Best Match: ", best_match)


    match_name, score, _ = best_match
    found_product = name_map[match_name]

    found_product = grocy.product(found_product.id)
    if found_product is None:
        return {
            "error": "Product not found",
        }
    else:
        return found_product


def consumer_amount_per_name(product_name, amount):
    found_product = get_prod_from_stock(product_name)
    logger.debug("Found Product: ", str(found_product))

    if isinstance(found_product, Product):
        logger.debug(found_product)
        grocy.consume_product(found_product.id, amount)
        return {
            "name": found_product.name,
            "removed_amount": amount,
            "remaining_amount": found_product.available_amount-float(amount),
            "unit_singular": found_product.default_quantity_unit_purchase.name,
            "unit_plural": found_product.default_quantity_unit_purchase.name_plural,
        }
    else:
        return {
            "error": "Product not found",
        }


def stock_shoppinglist_removeProduct(product_name, amount):
    found_product = get_prod_from_stock(product_name)
    logger.debug("Found Product: ", str(found_product.name))

    if isinstance(found_product, Product):
        grocy.remove_product_in_shopping_list(found_product.id, 1, amount)
        return {
            "name": found_product.name,
            "removed_amount": amount,
        }
    else:
        return {
            "error": "Product not found",
        }

def stock_shoppinglist_addProduct(product_name, amount):
    found_product = get_prod_from_stock(product_name)
    logger.debug("Found Product: ", str(found_product.name))

    if isinstance(found_product, Product):
        grocy.add_product_to_shopping_list(found_product.id, 1, amount)
        return {
            "name": found_product.name,
            "added_amount": amount,
        }
    else:
        return {
            "error": "Product not found",
        }

def get_shoppinglist():
    theList =  grocy.shopping_list(True)
    result= []
    for item in theList:
        product = item.product

        qu_conversionfactor = product.qu_conversion_factor_purchase_to_stock
        amount_on_list = math.ceil(item.amount / qu_conversionfactor)

        serialized_item = {
            'amount_on_list': amount_on_list,
            'name': product.name if hasattr(product, 'name') else None,
            'amount_in_stock': product.available_amount  if hasattr(product, 'available_amount') else None,
            "unit_singular": product.default_quantity_unit_purchase.name,
            "unit_plural": product.default_quantity_unit_purchase.name_plural,
            # Add any other attributes you need
        }
        result.append(serialized_item)

    logger.debug(result)
    return result


def get_amount_per_name(product_name):
    found_product = get_prod_from_stock(product_name)
    logger.debug("Found Product: ", str(found_product))

    if isinstance(found_product, Product):
        logger.debug(found_product)
        return {
            "name": found_product.name,
            "amount": found_product.available_amount,
            "unit_singular": found_product.default_quantity_unit_purchase.name,
            "unit_plural": found_product.default_quantity_unit_purchase.name_plural,
        }
    else:
        return {
            "error": "Product not found",
        }
