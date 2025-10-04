# Page snapshot

```yaml
- generic [ref=e4]:
  - generic [ref=e5]:
    - img [ref=e7]
    - heading "Sign in to your account" [level=2] [ref=e10]
    - paragraph [ref=e11]:
      - text: Or
      - link "create a new account" [ref=e12] [cursor=pointer]:
        - /url: /register
  - generic [ref=e13]:
    - generic [ref=e14]:
      - generic [ref=e15]:
        - generic [ref=e16]: Username
        - generic [ref=e17]:
          - generic:
            - img
          - textbox "Username" [ref=e18]
      - generic [ref=e19]:
        - generic [ref=e20]: Password
        - generic [ref=e21]:
          - generic:
            - img
          - textbox "Password" [ref=e22]
    - button "Sign in" [ref=e24] [cursor=pointer]
    - generic [ref=e25]:
      - generic [ref=e30]: Demo Credentials
      - generic [ref=e31]:
        - generic [ref=e32]:
          - strong [ref=e33]: "Staff:"
          - text: admin / admin123
        - generic [ref=e34]:
          - strong [ref=e35]: "Customer:"
          - text: customer / customer123
```