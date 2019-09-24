import random
import string
from models.cats_and_products import Category, Product, Texts
from mongoengine import connect

random_bool = (True, False)


def random_string(str_len=20):
	letters = string.ascii_letters
	return ''.join(random.choice(letters) for i in range(str_len))


def seed_and_get_categories(num_of_cats):
	category_list = []
	for i in range(num_of_cats):
		cat = Category(title=random_string()).save()
		category_list.append(cat)
	return category_list


def seed_products(num_of_products, list_of_cats):
	for i in range(num_of_products):
		product = dict(
			title=random_string(),
			description=random_string(),
			price=random.randint(1000, 100 * 1000),
			quantity=random.randint(0, 100),
			is_available=random.choice(random_bool),
			is_discount=random.choice(random_bool),
			weight=random.uniform(0, 100),
			width=random.uniform(0, 100),
			height=random.uniform(0, 100),
			category=random.choice(list_of_cats)
		)
		Product(**product).save()


def seed_products_with_image():
	products = Product.objects.all()

	for i in products:
		with open(r'product-icon-8.jpg', 'rb') as image:
			i.image.put(image)
			i.save()


if __name__ == '__main__':
	connect('bot_shop')
	seed_products_with_image()
	# p = Product.objects.all().first()
	# print(p.image.get())
	# cats = seed_and_get_categories(6)
	# products = seed_products(50, cats)

	# text = dict(
	#     title='Greetings',
	#     text=random_string(2000)
	# )
	# Texts(**text).save()
	# cats = seed_and_get_categories(10)
	# seed_products(50, cats)
	# CREATING SUB CATS
	# cat_obj = Category.objects.all().first()
	# cats = seed_and_get_categories(3)
	# cat_obj.sub_categories = cats
	# print(cat_obj.save())
