function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('Start Parsing').addItem('bet99-smarkets','runBet99Smarkets').addToUi();
}

function runBet99Smarkets() {
  console.log('Success');
  // var ui = SpreadsheetApp.getUi();
  // ui.alert('😃 Success');
}

function requestToScrapePair(pair) {
  var sheet = SpreadsheetApp.getActiveSheet();
  const sheetName = sheet.getName();

  const serverIp = '154.38.162.194'
  const url = `http://${serverIp}/scrapingPair/${pair}/${sheetName}`
  var options = {
    'method': 'get',
    'accept': 'application/json',
    'contentType': 'application/json',
    'headers': {'Authorization': 'Bearer f8443e0def04edab11a5325f1f3d2e54d15d8418b0816e1499e685a08656a71c'}
  };

  const response = UrlFetchApp.fetch(url, options);
  const content = JSON.parse(response.getContentText());
  console.log(`[${sheetName}] Sended request to scrape pair ${pair} ${serverIp}. Body: ${content}`);

  var ui = SpreadsheetApp.getUi();

  if (content.status == 'ok') {
    ui.alert(`😃 Success sended request to scrape ${pair}. Please waiting ⏰`);
  } else {
    ui.alert(`⚠️ Something went wrong with pair ${pair}`)
  };
}
