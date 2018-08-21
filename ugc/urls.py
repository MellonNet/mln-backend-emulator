from django.urls import path

from . import views

urlpatterns = [
	path("PrivateView/gallery.asmx/gallerySearchAllDataUser", views.search_all_data),
	path("PrivateView/gallery.asmx/gallerySearchAllDataGalleryItemUser", views.search_all_data_gallery_item),
	path("PrivateView/gallery.asmx/gallerySearchFactoryItemList", views.search_factory_item_list),
	path("PrivateView/gallery.asmx/gallerySearchFactoryItem", views.search_factory_item),
	path("gallery", views.gallery, name="gallery"),
	path("factory", views.factory, name="factory"),
]
