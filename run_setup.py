from controllers.system_controller import setup_demo

print("Running setup_demo...")
try:
    res = setup_demo()
    print("SUCCESS:", res)
except Exception as e:
    print("ERROR:", e)
