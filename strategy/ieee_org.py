import scrape

"""
ieexplore home
institutional sign in 'University of Melbourne'
https://sso.unimelb.edu.au/ u+p
url
click PDF
"""
async def apply(ctx, url, meta):
  ctx.log.info(f'{__name__} [{url}] in progress...')
  toplevel = scrape.domain(url)
  #ieeexplore
  url = 'https://ieeexplore.ieee.org/Xplore/home.jsp'
  await ctx.page.goto(url)



