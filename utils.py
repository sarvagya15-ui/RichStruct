import json 
 
def generate_product_jsonld(data): 
    """Generates JSON-LD for a Product.""" 
    schema = { 
        "@context": "https://schema.org/", 
        "@type": "Product", 
        "name": data.get('name'), 
        "image": [data.get('image')], 
        "description": data.get('description'), 
        "brand": { 
            "@type": "Brand", 
            "name": data.get('brand') 
        }, 
        "offers": { 
            "@type": "Offer", 
            "url": data.get('url'), 
            "priceCurrency": data.get('priceCurrency'), 
            "price": data.get('price'), 
            "availability": data.get('availability'), 
            "itemCondition": "https://schema.org/NewCondition" 
        } 
    } 
    return schema 
 
def generate_faq_jsonld(questions, answers): 
    """Generates JSON-LD for an FAQ Page.""" 
    main_entity = [] 
    for q, a in zip(questions, answers): 
        if q.strip() and a.strip(): 
            main_entity.append({ 
                "@type": "Question", 
                "name": q.strip(), 
                "acceptedAnswer": { 
                    "@type": "Answer", 
                    "text": a.strip() 
                } 
            }) 
     
    schema = { 
        "@context": "https://schema.org", 
        "@type": "FAQPage", 
        "mainEntity": main_entity 
    } 
    return schema 
 
def generate_course_jsonld(data): 
    """Generates JSON-LD for a Course.""" 
    schema = { 
        "@context": "https://schema.org", 
        "@type": "Course", 
        "name": data.get('name'), 
        "description": data.get('description'), 
        "provider": { 
            "@type": "Organization", 
            "name": data.get('provider_name'), 
            "sameAs": data.get('provider_url') 
        } 
    } 
    return schema