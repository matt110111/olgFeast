# Page snapshot

```yaml
- generic [ref=e4]:
  - generic [ref=e5]:
    - img [ref=e7]
    - heading "Sign in to your account" [level=2] [ref=e9]
    - paragraph [ref=e10]:
      - text: Or
      - link "create a new account" [ref=e11] [cursor=pointer]:
        - /url: /register
  - generic [ref=e12]:
    - generic [ref=e13]:
      - generic [ref=e14]:
        - generic [ref=e15]: Username
        - generic [ref=e16]:
          - generic:
            - img
          - textbox "Username" [ref=e17]
      - generic [ref=e18]:
        - generic [ref=e19]: Password
        - generic [ref=e20]:
          - generic:
            - img
          - textbox "Password" [ref=e21]
    - button "Sign in" [ref=e23] [cursor=pointer]
    - generic [ref=e24]:
      - generic [ref=e29]: Demo Credentials
      - generic [ref=e30]:
        - generic [ref=e31]:
          - strong [ref=e32]: "Staff:"
          - text: admin / admin123
        - generic [ref=e33]:
          - strong [ref=e34]: "Customer:"
          - text: customer / customer123
```