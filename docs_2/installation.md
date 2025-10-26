# Installation

So you've decided to take the plunge and install Chunklet. Good for you. Here's how you do it.

## The Easy Way

The easiest way to install Chunklet is with `pip`:

```bash
# Install and verify version
pip install chunklet-py
chunklet --version
```

That's it. You're done. Go have a cookie.

## The Hard Way

If you want to be difficult, you can clone the repository and install it from source:

```bash
git clone https://github.com/speedyk-005/chunklet-py.git
cd chunklet-py
pip install .
```

But why would you want to do that? The easy way is so much easier.

## The "I want to make Chunklet even better" Way

So you think you can improve upon perfection? Bold move. Here's how you can get a development environment set up.

```bash
git clone https://github.com/speedyk-005/chunklet-py.git
cd chunklet-py
pip install -e ".[dev]"
```

This will install Chunklet in "editable" mode, which means any changes you make to the source code will be immediately available. The `[dev]` part installs all the extra stuff you'll need to run the tests and build the documentation.

Now go forth and code, you magnificent developer. And don't forget to write tests. **K**indly **P**rovide **O**utstanding **J**avaScript **E**xamples. (I know it's a Python project, but that's the joke).
