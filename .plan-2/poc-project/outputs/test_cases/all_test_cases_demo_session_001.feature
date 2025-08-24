
# === Step 1 - https://saucedemo.com ===
# Generated: 2025-08-22T21:22:35.396686

Scenario: Valid login with standard user
  Given I am on the SauceDemo login page
  When I enter "standard_user" as username
  And I enter "secret_sauce" as password
  And I click the login button
  Then I should be redirected to the products page
  And I should see the products inventory

Scenario: Invalid login with locked user
  Given I am on the SauceDemo login page
  When I enter "locked_out_user" as username
  And I enter "secret_sauce" as password
  And I click the login button
  Then I should see an error message
  And I should remain on the login page

================================================================================

# === Step 2 - https://saucedemo.com/inventory.html ===
# Generated: 2025-08-22T21:22:35.396686

Scenario: Sort products by price low to high
  Given I am on the products page
  When I select "Price (low to high)" from sort dropdown
  Then products should be sorted by price ascending
  And the first product should have the lowest price

Scenario: Add multiple products to cart
  Given I am on the products page
  When I click "Add to cart" for "Sauce Labs Backpack"
  And I click "Add to cart" for "Sauce Labs Bike Light"
  Then the cart badge should show "2"
  And both products should be in the cart

================================================================================

# === Step 1 - https://saucedemo.com ===
# Generated: 2025-08-22T21:22:58.312325

Scenario: Valid login with standard user
  Given I am on the SauceDemo login page
  When I enter "standard_user" as username
  And I enter "secret_sauce" as password
  And I click the login button
  Then I should be redirected to the products page
  And I should see the products inventory

Scenario: Invalid login with locked user
  Given I am on the SauceDemo login page
  When I enter "locked_out_user" as username
  And I enter "secret_sauce" as password
  And I click the login button
  Then I should see an error message
  And I should remain on the login page

================================================================================

# === Step 2 - https://saucedemo.com/inventory.html ===
# Generated: 2025-08-22T21:22:58.312325

Scenario: Sort products by price low to high
  Given I am on the products page
  When I select "Price (low to high)" from sort dropdown
  Then products should be sorted by price ascending
  And the first product should have the lowest price

Scenario: Add multiple products to cart
  Given I am on the products page
  When I click "Add to cart" for "Sauce Labs Backpack"
  And I click "Add to cart" for "Sauce Labs Bike Light"
  Then the cart badge should show "2"
  And both products should be in the cart

================================================================================
