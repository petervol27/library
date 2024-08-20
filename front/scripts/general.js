const logout = async () => {
  localStorage.removeItem('jwt_token');
  const response = await axios.get(
    'https://library-klmc.onrender.com/logout/',
    {
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
    }
  );
  if (response) {
    window.location.href = '../index.html';
  }
};
const getSession = async () => {
  const token = localStorage.getItem('jwt_token');
  if (token) {
    const response = await axios.get(
      'https://library-klmc.onrender.com/get_session/',
      {
        withCredentials: true,
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
      }
    );
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
  const isActive = window.location.pathname != '/library/front/main.html';
  const activeClass = isActive ? 'active' : '';
  if (user) {
    document.getElementById('user-info').textContent = `Hello, ${user['name']}`;
  } else {
    window.location.href = '../index.html';
  }
  if (user.id != 1) {
    const navItem = document.createElement('li');
    navItem.classList.add('nav-item');
    navItem.innerHTML = `<a class="nav-link ${activeClass}" href="./myBooks.html">My Books</a>`;
    navbar.appendChild(navItem);
  } else {
    const navItem = document.createElement('li');
    navItem.classList.add('nav-item');
    navItem.innerHTML = `<a class="nav-link ${activeClass}" href="./readers.html">Readers List</a>`;
    navbar.appendChild(navItem);
  }
};

const getBooks = async function () {
  const response = await axios.get('https://library-klmc.onrender.com/books/', {
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
  const response = await axios.post(
    'https://library-klmc.onrender.com/books_rented/',
    {
      userId: user.id,
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
    }
  );
  return response.data;
};

const returnBook = async (bookId) => {
  const response = await axios.get(
    `https://library-klmc.onrender.com/return_book/${bookId}`,
    {
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
    }
  );
  alert(response.data.message);
  window.location.reload();
};
