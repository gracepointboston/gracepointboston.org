all:
	@make sync_site_assets
	@make sync_code_blocks
	@make sync_with_github

init:
	brew install gh python3

sync_code_blocks:
	@for url in $$(curl https://www.gracepointboston.org/sitemap.xml 2>/dev/null | grep "<loc>" | sed -re "s/<\/?loc>//g" -e "s/^ +//g" | sort | uniq); do python3 scripts/extract_code_blocks.py $${url}; done

sync_site_assets:
	@python3 scripts/extract_site_assets.py

sync_with_github:
	@git branch -D review || true
	@git checkout -b review
	@git add .
	@git commit -m "Submitting latest work for review"
	@git push --set-upstream origin review
	@gh pr create --fill
