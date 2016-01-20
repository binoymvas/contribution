import chef

chefapi=chef.ChefAPI('http://38.113.206.18:4000', './horizon.pem', 'horizon')

for name in chef.Node.list(api=chefapi):
	print chef.Node(name).attributes.items()

