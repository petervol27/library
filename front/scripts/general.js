const logout = async () => {
  localStorage.removeItem('jwt_token');
  const response = await axios.get('http://127.0.0.1:9000/logout/', {
    withCredentials: true,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
  });
  if (response) {
    window.location.href = '../index.html';
  }
};
const getSession = async () => {
  const token = localStorage.getItem('jwt_token');
  if (token) {
    const response = await axios.get('http://127.0.0.1:9000/get_session/', {
      withCredentials: true,
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
    });
    if (response.data.message != 'Token found') {
      window.location.href = '../index.html';
    } else {
      const user = { id: response.data.userId, name: response.data.userName };
      return user;
    }
  } else {
    window.location.href = '../index.html';
  }
};

const checkLogin = async () => {
  const user = await getSession();
  const navbar = document.getElementById('navbar');
  const isActive = (page) => {
    const currentPath = window.location.pathname;
    return currentPath.includes(page) ? 'active' : '';
  };
  const homePage = document.createElement('li');
  homePage.classList.add('nav-item');
  homePage.innerHTML = `<a class="nav-link ${isActive(
    'main.html'
  )}" href="./main.html">Home</a>`;
  navbar.appendChild(homePage);
  if (user) {
    document.getElementById('user-info').textContent = `Hello, ${user['name']}`;
  } else {
    window.location.href = '../index.html';
  }
  if (user.id != 1) {
    const navItem = document.createElement('li');
    navItem.classList.add('nav-item');
    navItem.innerHTML = `<a class="nav-link ${isActive(
      'mybooks.html'
    )}" href="./myBooks.html">My Books</a>`;
    navbar.appendChild(navItem);
  } else {
    const navItem = document.createElement('li');
    const navItem2 = document.createElement('li');
    navItem.classList.add('nav-item');
    navItem2.classList.add('nav-item');
    navItem.innerHTML = `<a class="nav-link ${isActive(
      'readers.html'
    )}" href="./readers.html">Readers List</a>`;
    navItem2.innerHTML = `<a class="nav-link ${isActive(
      'addBook.html'
    )}" href="./addBook.html">Add Book</a>`;
    navbar.appendChild(navItem);
    navbar.appendChild(navItem2);
  }
};

const getBooks = async function () {
  const response = await axios.get('http://127.0.0.1:9000/books/', {
    withCredentials: true,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
  });
  return response.data;
};
const checkRented = async () => {
  const user = await getSession();
  const response = await axios.post('http://127.0.0.1:9000/books_rented/', {
    userId: user.id,
    withCredentials: true,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
  });
  return response.data;
};

const returnBook = async (bookId) => {
  const token = localStorage.getItem('jwt_token');
  const response = await axios.get(
    `http://127.0.0.1:9000/return_book/${bookId}/`,
    {
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        Authorization: `Bearer ${token}`,
      },
    }
  );
  alert(response.data.message);
  window.location.reload();
};

const checkAdmin = async () => {
  const user = await getSession();
  if (user.id != 1) {
    window.location.href = './main.html';
  }
};
