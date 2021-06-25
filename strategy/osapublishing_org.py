import scrape

async def apply(ctx, url):
  ctx.log.info(f'{__name__} [{url}] in progress...')
  toplevel = scrape.domain(url)
  ctx.log.info(f'Visiting %s for eventual cookies' % toplevel)
  ctx.log.info(f'Going to: {url}')
  #await ctx.page.goto(url)
  ctx.log.info('Arrived on page')
  ctx.log.info(f'Trying to download from: {url}')
  #await ctx.page.screenshot({'path': './sample.png'})
