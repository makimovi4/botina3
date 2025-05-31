class ItemInfo:
    def __init__(self, item_id, item_title, item_price, item_price_currency, item_url, location, country_iso_code,
                 item_view_count, item_time_delta, profile_created_delta, profile_item_count, profile_rating,
                 profile_feedbacks, given_item_count, taken_item_count, profile_url, profile_login, description,
                 item_photo_url):
        self.item_id = item_id
        self.item_title = item_title
        self.item_price = item_price
        self.item_price_currency = item_price_currency
        self.item_url = item_url
        self.location = location
        self.country_iso_code = country_iso_code
        self.item_view_count = item_view_count
        self.item_time_delta = item_time_delta
        self.profile_created_delta = profile_created_delta
        self.profile_item_count = profile_item_count
        self.profile_rating = profile_rating
        self.profile_feedbacks = profile_feedbacks
        self.given_item_count = given_item_count
        self.taken_item_count = taken_item_count
        self.profile_url = profile_url
        self.profile_login = profile_login
        self.description = description
        self.item_photo_url = item_photo_url
