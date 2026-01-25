from pydantic import BaseModel, HttpUrl

class ProductImageCreate(BaseModel):
    image_url: HttpUrl   #only valid URL allowed for image_url
    
class ProductImageResponse(BaseModel):
    id: int
    image_url: HttpUrl
    is_primary: bool = False  
    
    """why?
    UI ko btana hota hai:
    kaunsi image tumbnail hai
    kaunsi image primary hai
    """
    class Config:
        from_attributes = True
        """FastAPI ORM object (User) -
        schema mai convert karta hai
        
        from attributes = true btata hai ki yeh ORM object se data lega na ki dict se
        """
        
# image add karna = product image ka ek action issliye humne alag schema banaya hai jo sirf image_url leta hai, alag endpoint hoga , alag focused ressponsibility hoga