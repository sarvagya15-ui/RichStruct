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
            errors.append("Product [Google]: 'name' is a mandatory field.")
        if not data.get('image'):
            warnings.append("Product [Google]: 'image' is missing. Without an image, your page cannot show as a rich result.")
        if 'description' not in data or len(data.get('description', '')) < 50:
            warnings.append("Product [Google]: 'description' is short. Google recommends at least 50 characters.")
        if 'offers' not in data:
            errors.append("Product [Google]: Missing 'offers' object. Price and availability are required for Rich Results.")
        else:
            offers = data.get('offers')
            if not offers.get('price'):
                errors.append("Product [Google]: 'price' is missing inside 'offers'.")
            if not offers.get('priceCurrency'):
                errors.append("Product [Google]: 'priceCurrency' is missing. Use 3-letter codes like 'USD' or 'INR'.")
        
        if 'aggregateRating' not in data:
            warnings.append("Product [Google]: 'aggregateRating' field is missing. Ratings help increase click-through rates.")

    # Specific Rules for FAQ
    elif schema_type == 'FAQPage':
        if 'mainEntity' not in data or not isinstance(data.get('mainEntity'), list):
            errors.append("FAQ [Google]: 'mainEntity' must be a list of questions.")
        else:
            entities = data.get('mainEntity')
            if len(entities) < 2:
                warnings.append("FAQ [Google]: It is recommended to have at least 2 questions for a better rich result display.")
            for i, item in enumerate(entities):
                if not item.get('name') or len(item.get('name')) < 10:
                    warnings.append(f"FAQ [Google]: Question #{i+1} is very short. Aim for clear, helpful questions.")

    return errors, warnings
