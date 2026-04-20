def validate_schema_rules(data): 
    """ 
    Checks if the JSON-LD follows basic schema rules. 
    Returns a list of errors and warnings. 
    """ 
    errors = [] 
    warnings = [] 
     
    # Check for @context and @type 
    if '@context' not in data: 
        errors.append("Missing '@context' field. It should usually be 'https://schema.org'.") 
     
    if '@type' not in data: 
        errors.append("Missing '@type' field. The generator doesn't know what this is.") 
        return errors, warnings # Can't continue without type 
     
    schema_type = data.get('@type') 
     
    # Specific Rules for Product 
    if schema_type == 'Product': 
        if not data.get('name'): 
            errors.append("Product must have a 'name'.") 
        if not data.get('image'): 
            warnings.append("Adding an 'image' is highly recommended for Google Rich Results.") 
        if 'offers' not in data: 
            warnings.append("Missing 'offers'. Google usually expects price and availability for Products.") 
        else: 
            offers = data.get('offers') 
            if not offers.get('price'): 
                errors.append("Product 'offers' must include a 'price'.") 
            if not offers.get('priceCurrency'): 
                errors.append("Product 'offers' must include a 'priceCurrency'.") 
 
    # Specific Rules for FAQ 
    elif schema_type == 'FAQPage': 
        if 'mainEntity' not in data: 
            errors.append("FAQPage must have a 'mainEntity'.") 
        else: 
            entities = data.get('mainEntity') 
            if not entities or len(entities) == 0: 
                errors.append("FAQPage must contain at least one Question.") 
 
    return errors, warnings

