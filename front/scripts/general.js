const logout = async () => {
  const response = await axios.get('http://127.0.0.1:9000/logout/', {
    withCredentials: true,
  });
  if (response) {
    window.location.href = 'index.html';
  }
};
const getSession = async () => {
  const response = await axios.get('http://127.0.0.1:9000/get_session/', {
    withCredentials: true,
  });
  const user = response.data.reader;
  return user;
};

const checkLogin = async () => {
  const user = await getSession();
  const navbar = document.getElementById('navbar');
  const isActive = window.location.pathname !== '/front/main.html';
  const activeClass = isActive ? 'active' : '';
  if (user) {
    document.getElementById('user-info').textContent = `Hello, ${user['name']}`;
  } else {
    window.location.href = 'index.html';
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
  const response = await axios.get('http://127.0.0.1:9000/books/');
  return response.data;
};
const checkRented = async () => {
  const user = await getSession();
  const response = await axios.post('http://127.0.0.1:9000/books_rented/', {
    userId: user.id,
  });
  return response.data;
};

const returnBook = async (bookId) => {
  const response = await axios.get(
    `http://127.0.0.1:9000/return_book/${bookId}`,
    {
      withCredentials: true,
    }
  );
  alert(response.data.message);
};
