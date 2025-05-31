def search_text_to_link(search_text, while_iter, domain_zone):
    search_text = search_text.replace("catalog?", "vetements?")
    if search_text.startswith("https://www.vinted."):
        str_index = search_text.find('/vetements?')
        unique_search = f'/vetements?page={while_iter}&per_page=50'
        if search_text.endswith('/women'):
            unique_search += '&catalog[]=1904'
        elif search_text.endswith('/men'):
            unique_search += '&catalog[]=5'
        elif search_text.endswith('kids'):
            unique_search += '&catalog[]=1193'
        elif search_text.endswith('/home'):
            unique_search += '&catalog[]=1918'
        elif search_text.endswith('/entertainment'):
            unique_search += '&catalog[]=2309'
        elif search_text.endswith('/pet-care'):
            unique_search += '&catalog[]=2093'
        elif str_index > 0:
            search_text_without_host = search_text[str_index + 11:]
            search_splited = search_text_without_host.split('&')
            for search_splited_item in search_splited:
                if search_splited_item.startswith('per_page='):
                    search_splited.remove(search_splited_item)
                    continue
                elif search_splited_item.startswith('page='):
                    search_splited.remove(search_splited_item)
                    continue
                unique_search += f'&{search_splited_item}'
        else:
            return False
        parsing_url = f"https://www.vinted.{domain_zone}{unique_search}"
    else:
        parsing_url = f"https://www.vinted.{domain_zone}/vetements?page={while_iter}&per_page=50&search_text={search_text}&order=newest_first"
    return parsing_url


def change_domain(link, domain_to_change):
    first = link[:19]
    second = link[19:]
    third = second[second.find('/'):]
    new_link = first + domain_to_change + third
    return new_link


if __name__ == '__main__':
    asd = search_text_to_link(
        'https://www.vinted.pl/vetements?catalog[]=10&order=newest_first&status[]=1&brand_id[]=60&color_id[]=3&size_id[]=1226',
        1, 'sk')
    print(asd)
