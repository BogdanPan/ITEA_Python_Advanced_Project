import telebot
from bot import config
from models.cats_and_products import (Texts, Category, Product, Cart, OrdersHistory)
from models.user_model import User
from telebot.types import (
	InlineKeyboardButton,
	InlineKeyboardMarkup,
	ReplyKeyboardMarkup)
from bson import ObjectId
from mongoengine import connect

bot = telebot.TeleBot(config.TOKEN)
connect('bot_shop')


def get_by_lang(text, lang):
	try:
		final_product = Texts.get_text(text + '_' + lang)
		return final_product

	except AttributeError:
		try:
			final_product = Texts.get_text(text + '_en')
			return final_product

		except AttributeError:
			final_product = 'Error'
			return final_product


@bot.message_handler(commands=["start"])
def start(message):
	User.get_or_create_user(message)
	lang = message.from_user.language_code
	cat_button_text = get_by_lang('category_text', lang)
	info_button_text = get_by_lang('info_text', lang)
	news_button_text = get_by_lang('news_text', lang)
	greetings = get_by_lang('greetings', lang)
	bot.send_message(message.chat.id, greetings)
	main_kb = InlineKeyboardMarkup()
	buttons_list = list()
	buttons_list.append(InlineKeyboardButton(text=cat_button_text, callback_data='cats'))
	buttons_list.append(InlineKeyboardButton(text=news_button_text, callback_data='news'))
	buttons_list.append(InlineKeyboardButton(text=info_button_text, callback_data='info'))
	main_kb.add(*buttons_list)
	bot.send_message(message.chat.id, text='_', reply_markup=main_kb)


@bot.callback_query_handler(func=lambda call: call.data == 'cats')
def cat_handler(call):
	bot.delete_message(call.message.chat.id, call.message.message_id)
	cats_kb = InlineKeyboardMarkup()
	cats_buttons = []
	all_cats = Category.objects.all()
	for i in all_cats:
		cats_buttons.append(InlineKeyboardButton(text='>>' + i.title, callback_data='category_' + str(i.id)))
	cats_kb.add(*cats_buttons)
	cats_kb.add(InlineKeyboardButton(text='Return', callback_data='main_menu'))
	bot.send_message(call.message.chat.id, text='Categories', reply_markup=cats_kb)


@bot.callback_query_handler(func=lambda call: call.data == 'main_menu')
def main_menu(call):
	lang = call.from_user.language_code
	cat_button_text = get_by_lang('category_text', lang)
	info_button_text = get_by_lang('info_text', lang)
	news_button_text = get_by_lang('news_text', lang)
	main_kb = InlineKeyboardMarkup()
	buttons_list = list()
	buttons_list.append(InlineKeyboardButton(text=cat_button_text, callback_data='cats'))
	buttons_list.append(InlineKeyboardButton(text=news_button_text, callback_data='news'))
	buttons_list.append(InlineKeyboardButton(text=info_button_text, callback_data='info'))
	main_kb.add(*buttons_list)
	bot.send_message(call.message.chat.id, text='_', reply_markup=main_kb)
	bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'category')
def product_by_cat(call):
	lang = call.from_user.language_code
	basket_text = get_by_lang('basket', lang)
	detailed = get_by_lang('detailed', lang)
	bot.delete_message(call.message.chat.id, call.message.message_id)
	cat = Category.objects.filter(id=call.data.split('_')[1]).first()
	products = cat.category_products
	for p in products:
		products_kb = InlineKeyboardMarkup(row_width=2)
		products_kb.add(InlineKeyboardButton(
			text=basket_text,
			callback_data='addtocart_' + str(p.id)

		),
			InlineKeyboardButton(
				text=detailed,
				callback_data='product_' + str(p.id)
			)
		)
		title = f'<b>{p.title}</b>'
		description = f'\n\n<i>{p.description}</i>'
		products_kb.add(InlineKeyboardButton(text='Close', callback_data='delete_this'))
		bot.send_photo(
			call.message.chat.id,
			p.image.get(),
			caption=title + description,
			reply_markup=products_kb,
			parse_mode='HTML'
		)
	back_kb = InlineKeyboardMarkup()
	back_kb.add(InlineKeyboardButton(text='Return', callback_data='main_menu'))
	bot.send_message(call.message.chat.id, text='_', reply_markup=back_kb)


@bot.callback_query_handler(func=lambda call: call.data == 'delete_this')
def delete_and_go_back(call):
	bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'product')
def brief_info(call):
	bot.delete_message(call.message.chat.id, call.message.message_id)
	product = Product.get_by_id(call.data.split('_')[1])
	small_kb = InlineKeyboardMarkup()
	small_kb.add(InlineKeyboardButton(text='Close', callback_data='delete_this'))
	bot.send_message(
		call.message.chat.id,
		text=(
			f"Item: {product.title}\n"
			f"Price: {product.price}\n"
			f"Quantity:{product.quantity}\n"
			f"Weight: {product.weight}\n"
			f"Width: {product.width}\n"
			f"Height {product.height}\n"
		),
		reply_markup=small_kb
	)


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'addtocart')
def add_to_card(call):
	Cart.create_or_append_to_cart(product_id=call.data.split('_')[1], user_id=call.message.chat.id)
	cart = Cart.objects.all().first()


@bot.message_handler(commands=['cart'])
def show_cart(message):
	current_user = User.objects.get(user_id=message.chat.id)
	cart = Cart.objects.filter(user=current_user, is_archived=False).first()

	if not cart:
		bot.send_message(message.chat.id, 'Корзина пустая')
		return

	if not cart.products:
		bot.send_message(message.chat.id, 'Корзина пустая')

	for product in cart.products:
		remove_kb = InlineKeyboardMarkup()
		remove_button = InlineKeyboardButton(text='Удалить продукт с корзины',
											 callback_data='rmproduct_' + str(product.id))
		remove_kb.add(remove_button)
		bot.send_message(message.chat.id, product.title,
						 reply_markup=remove_kb)

	submit_kb = InlineKeyboardMarkup()
	submit_button = InlineKeyboardButton(
		text='Оформить заказ',
		callback_data='submit'
	)
	submit_kb.add(submit_button)
	bot.send_message(message.chat.id, 'Подтвердите Ваш заказ', reply_markup=submit_kb)


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'rmproduct')
def rm_product_from_cart(call):
	current_user = User.objects.get(user_id=call.message.chat.id)
	cart = Cart.objects.get(user=current_user)
	cart.update(pull__products=ObjectId(call.data.split('_')[1]))
	bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'submit')
def submit_cart(call):
	current_user = User.objects.get(user_id=call.message.chat.id)
	cart = Cart.objects.filter(user=current_user, is_archived=False).first()
	cart.is_archived = True

	order_history = OrdersHistory.get_or_create(current_user)
	order_history.orders.append(cart)
	bot.send_message(call.message.chat.id, 'Спасибо за заказ!')
	cart.save()
	order_history.save()


# print(Product.get_by_id(call.data.split('_')[1]).title)
# bot.send_message(call.message.chat.id, text=Product.get_price_by_title(call.data.split('_')[1]).price)


if __name__ == '__main__':
	bot.polling()
