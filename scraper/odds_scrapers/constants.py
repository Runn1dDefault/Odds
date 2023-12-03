# bet99 constants
BET99_BASE_URL = 'https://bet99.com/'
BET99_CATEGORY_URL = 'https://bet99.com/en/sport-betting#/sport/{}'
BET99_SUBCATEGORIES_URL = 'https://sb2frontend-altenar2.biahosted.com/api/SportsBook/GetMenuBySport' \
                    '?timezoneOffset=-360&langId=8&skinName=bet99&configId=12&culture=en-GB&countryCode=US' \
                    '&deviceType=Desktop&numformat=en&integration=bet99&sportId={sport_id}&period=periodall' \
                    '&startDate={start_time}&endDate={end_time}'
BET99_EVENT_URL = 'https://bet99.com/en/sport-betting#/event/{sport_id}/{category_id}/0/all/{event_id}'
BET99_EVENTS_TYPES_URL = 'https://sb2frontend-altenar2.biahosted.com/api/SportsBook/GetEventTypes?' \
                   'timezoneOffset=-360&langId=8&skinName=bet99&configId=12&culture=en-GB' \
                   '&countryCode=US&deviceType=Desktop&numformat=en&integration=bet99' \
                   '&champids={champ_ids}&categoryids=0&sportids={sport_ids}&withLive=true&period=periodall' \
                   '&startDate={start_time}&endDate={end_time}'
BET99_EVENTS_LIST_URL = 'https://sb2frontend-altenar2.biahosted.com/api/Sportsbook/GetEvents?timezoneOffset=-360&langId=8' \
                  '&skinName=bet99&configId=12&culture=en-GB&countryCode=US&deviceType=Desktop&numformat=en' \
                  '&integration=bet99&sportids={sport_ids}&categoryids=0&champids={champ_ids}' \
                  '&group={group}&period=periodall&withLive=false' \
                  '&outrightsDisplay={outrights_display}&marketTypeIds=&couponType=0&marketGroupId=0' \
                  '&startDate={start_time}&endDate={end_time}'
BET99_EVENT_FIELDS = ('Money Line', '1x2')

# smarkets constants
SMARKETS_BASE_URL = 'https://smarkets.com/'
SMARKETS_SUBCATEGORIES_XPATH = '//ul[contains(@class, "listing")]//' \
                      'a[starts-with(@href, "/listing") or starts-with(@href, "/sport")]/@href'
SMARKETS_PAGE_ADDITIONS_TABS = '//div[contains(@class, "event-listing-sections-tabs")]/a/@href'
SMARKETS_EVENTS_XPATH = '//ul[contains(@class, "event-list")]/li'
SMARKETS_CONTRACTS_XPATH = '//div[contains(@class, "contract-items")]/span'
# SMARKETS_TEAM_XPATH = '//span[contains(@class, "contract-label") and not(contains(text(), "Draw"))' \
#                       'and not(contains(text(), "Yes")) and not(contains(text(), "No"))]/text()'
SMARKETS_TEAM_XPATH = '//span[contains(@class, "contract-label") and not(contains(text(), "Yes"))' \
                      ' and not(contains(text(), "No"))]/text()'
SMARKETS_LAY_XPATH = '//span[@class="bid"]/span[contains(@class, "price")]/text()'
