# AEGIS

AEGIS is an API that securely manages users, wallets, trading positions, and fund integrations for seamless interfaces.

<img src="https://github.com/smartswap-org/aegis/blob/d433ff2f9eae6c050a974553dfec1c3a59f814df/assets/logo.png" alt="AEGIS Logo" style="width:300px">

## Features

- User management: register, login, and manage user accounts
- Wallet management: create, update, and delete wallets
- Trading positions: manage trading positions with buy and sell functionalities
- Fund management: track and manage funds associated with bots

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/aegis.git
   cd aegis
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # on Windows use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment:
   Create a `.env` file in the root directory:
   ```
   FLASK_SECRET_KEY=your-secret-key
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=
   MYSQL_DB=smartswap
   MYSQL_PORT=3306
   ```

5. Start the API:
   ```bash
   python run.py
   ```

## Documentation
  See the whole doc by running the API and then by accessing `http://127.0.0.1:5001/`

## Tests
  ```bash
  pytest tests/test_routes.py -v
  ```

  ```Python
   tests/test_routes.py::test_home_route PASSED                                                                [  7%]
   tests/test_routes.py::test_register PASSED                                                                  [ 15%]
   tests/test_routes.py::test_login PASSED                                                                     [ 23%]
   tests/test_routes.py::test_logout PASSED                                                                    [ 30%]
   tests/test_routes.py::test_create_position PASSED                                                           [ 38%]
   tests/test_routes.py::test_get_positions PASSED                                                             [ 46%]
   tests/test_routes.py::test_get_position PASSED                                                              [ 53%]
   tests/test_routes.py::test_create_fund PASSED                                                               [ 61%]
   tests/test_routes.py::test_get_funds PASSED                                                                 [ 69%]
   tests/test_routes.py::test_get_fund PASSED                                                                  [ 76%]
   tests/test_routes.py::test_create_wallet PASSED                                                             [ 84%]
   tests/test_routes.py::test_get_wallet PASSED                                                                [ 92%]
   tests/test_routes.py::test_delete_wallet PASSED                                                             [100%]
   
   ========================================= 13 passed, 2 warnings in 0.14s ==========================================
   ```
