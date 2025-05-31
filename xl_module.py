from openpyxl import Workbook


def create_xl_file(item_list: list, domain_zone: str, user_id: int):
    wb = Workbook()
    ws = wb.active
    ws.append(['Title', 'Price', 'Seller Name', "Seller's ads quantity", 'Seen times', 'Ad link', 'Chat'])
    for item in item_list:
        ws.append([item.item_title,
                   f'{item.item_price} {item.item_price_currency}',
                   item.profile_login,
                   item.profile_item_count,
                   item.item_view_count,
                   item.item_url,
                   f"https://www.vinted.{domain_zone}/member/signup?button_name=message&ch=wd&item_id={item.item_id}&receiver_id={item.profile_url[item.profile_url.find('member/') + 7:item.profile_url.find('-')]}&ref_url=%2Fitems%2F{item.item_id}%2Fwant_it%2Fnew%3Fbutton_name%3Dmessage%26ch%3Dwd&receiver_id%3D{item.profile_url[item.profile_url.find('member/') + 7:item.profile_url.find('-')]}{item.profile_url}"
                   ])

    wb.save(f"swap/{user_id}.xlsx")


def create_txt_file(item_list: list, domain_zone: str, domain_to_change: str, user_id: int):
    final_str = ''
    for item in item_list:
        final_str += f"{item.item_url.replace(domain_zone.lower(),domain_to_change)}\n"
    with open(f"swap/{user_id}.txt", mode='w+') as file:
        file.write(final_str)
    file.close()


