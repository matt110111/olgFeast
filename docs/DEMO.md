# Four-kitchen demo

After running the demo setup below, open `/event` on the local app. Use **input1** through **input6** for the six
order-taking tablets. Use **kitchen1** through **kitchen4** for kitchen tablets;
they open Fried, Grilled, Cooked 1, and Cooked 2 respectively. These are volunteer
accounts. The organizer account manages recipes, stock, and reports. The existing
customer account remains a guest account. New demo station accounts use the
password supplied through `DEMO_STATION_PASSWORD`; keep it out of Git.

## Take an order

1. Choose **Menu / take orders** and the input station number.
2. Browse the full menu with Previous/Next, or filter by kitchen. Up to four menu tiles
   appear per page (two on shorter screens) so the menu does not run below the iPad viewport.
3. Add portions and an optional guest name or table.
4. Tap **Check order**. The check screen shows the total number of physical tickets.
5. Collect those tickets at this station, check **I collected … tickets**, then
   tap **Send to kitchen**.
6. One confirmation sends each item to its assigned kitchen. The receipt shows
   the shared check number and each kitchen's order number. Tap **Next guest**.

A mixed check is saved all at once. If the connection drops, **Retry same order**
recovers the same check and kitchen orders, even after reloading. Do not collect
tickets a second time. Each kitchen prepares and serves its own items. Voiding
one kitchen order returns only the tickets allocated to that kitchen order.

The order list can scroll inside its panel for a large order; the total and action
buttons stay on screen. Menu browsing uses pages. The compact layout is tested
at iPad portrait and landscape viewport sizes, with browser chrome accounted for
through the visible viewport height.

## Demo recipes and stock

The 14 existing menu items have demo recipes including ingredients and serving
supplies: plates, trays, bowls, cutlery, napkins, cups, lids, straws, and stirrers.
Starting stock provides 100 portions of each item assigned to a kitchen. These
are illustrative quantities for demonstrating depletion, not actual event counts.
Existing ticket values are retained.

- **Fried:** wings, with chicken wings, frying oil, sauce, trays, and napkins.
- **Grilled:** sausage and peppers sandwiches, salmon, and steak.
- **Cooked 1:** chicken Alfredo, garlic bread, and coffee.
- **Cooked 2:** vegetarian pasta, salad, desserts, and cold drinks.

The cooked areas also serve the demo sides and drinks. Each food has exactly one
kitchen assignment, which can be changed in **Menu & setup**. Recipes and stock
are editable there. **Event report** shows recipe-based estimated use and remaining
stock. Its order count counts kitchen orders; a check can create several kitchen
orders, while tickets and portions are counted once.

`fastapi_app/demo_setup.py` fills missing demo recipes, creates the four kitchens,
assigns the known demo foods, and adds starting stock once. It creates the ten
volunteer accounts only if absent and does not change existing passwords.
Pass `DEMO_STATION_PASSWORD` and optionally `DEMO_EVENT_ID` when running it.
