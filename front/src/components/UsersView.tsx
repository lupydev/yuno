import React, { useState } from 'react';
import { LayoutDashboard, Activity, Bell, Menu, Users, Edit2, Trash2, Plus, Search, X } from 'lucide-react';

const UsersView = () => {
    const [users, setUsers] = useState([
        { id: 'USR-001', name: 'Alice Johnson', email: 'alice.j@company.com', team: 'Software Development', role: 'Developer', status: 'active' },
        { id: 'USR-002', name: 'Bob Smith', email: 'bob.s@company.com', team: 'DevOps', role: 'Engineer', status: 'active' },
        { id: 'USR-003', name: 'Carol White', email: 'carol.w@company.com', team: 'Software Development', role: 'Senior Developer', status: 'active' },
        { id: 'USR-004', name: 'David Brown', email: 'david.b@company.com', team: 'QA Testing', role: 'QA Lead', status: 'active' },
        { id: 'USR-005', name: 'Emma Davis', email: 'emma.d@company.com', team: 'Product Management', role: 'Product Manager', status: 'inactive' },
        { id: 'USR-006', name: 'Frank Miller', email: 'frank.m@company.com', team: 'Software Development', role: 'Developer', status: 'active' },
        { id: 'USR-007', name: 'Grace Lee', email: 'grace.l@company.com', team: 'Infrastructure', role: 'SRE', status: 'active' },
        { id: 'USR-008', name: 'Henry Wilson', email: 'henry.w@company.com', team: 'Security', role: 'Security Engineer', status: 'active' },
    ]);

    const [searchTerm, setSearchTerm] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [modalMode, setModalMode] = useState('create');
    const [selectedUser, setSelectedUser] = useState(null);
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        team: '',
        role: '',
        status: 'active'
    });

    const teams = ['Software Development', 'DevOps', 'QA Testing', 'Product Management', 'Infrastructure', 'Security', 'Design', 'Data Science'];
    const roles = ['Developer', 'Senior Developer', 'Engineer', 'QA Lead', 'Product Manager', 'SRE', 'Security Engineer', 'Designer'];

    const filteredUsers = users.filter(user =>
        user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.team.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.id.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const openCreateModal = () => {
        setModalMode('create');
        setFormData({ name: '', email: '', team: '', role: '', status: 'active' });
        setSelectedUser(null);
        setShowModal(true);
    };

    const openEditModal = (user) => {
        setModalMode('edit');
        setFormData({
            name: user.name,
            email: user.email,
            team: user.team,
            role: user.role,
            status: user.status
        });
        setSelectedUser(user);
        setShowModal(true);
    };

    const handleCreate = () => {
        const newUser = {
            id: `USR-${String(users.length + 1).padStart(3, '0')}`,
            ...formData
        };
        setUsers([...users, newUser]);
        setShowModal(false);
    };

    const handleUpdate = () => {
        setUsers(users.map(user =>
            user.id === selectedUser.id ? { ...user, ...formData } : user
        ));
        setShowModal(false);
    };

    const handleDelete = (userId) => {
        if (window.confirm('Are you sure you want to delete this user?')) {
            setUsers(users.filter(user => user.id !== userId));
        }
    };

    const handleSave = () => {
        if (!formData.name || !formData.email || !formData.team || !formData.role) {
            alert('Please fill in all fields');
            return;
        }
        if (modalMode === 'create') {
            handleCreate();
        } else {
            handleUpdate();
        }
    };

    return (
        <div className="p-8 max-w-[1800px] mx-auto">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-white">User Management</h1>
                    <p className="text-slate-400 mt-1">Manage users and assign them to teams for error routing</p>
                </div>
                <button
                    onClick={openCreateModal}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium flex items-center gap-2 transition-colors"
                >
                    <Plus className="w-4 h-4" />
                    Add User
                </button>
            </div>

            <div className="mb-6 relative">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                    type="text"
                    placeholder="Search by name, email, team, or ID..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-12 pr-4 py-3 bg-slate-900 border border-slate-800 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-600"
                />
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-slate-800/50">
                        <tr>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">User ID</th>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Name</th>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Email</th>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Team</th>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Role</th>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Status</th>
                            <th className="px-6 py-4 text-right text-xs font-semibold text-slate-300 uppercase tracking-wider">Actions</th>
                        </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                        {filteredUsers.map((user) => (
                            <tr key={user.id} className="hover:bg-slate-800/30 transition-colors">
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className="text-sm font-mono text-slate-400">{user.id}</span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className="text-sm font-medium text-white">{user.name}</span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className="text-sm text-slate-300">{user.email}</span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                        <span className="inline-flex px-3 py-1 text-xs font-semibold rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                                            {user.team}
                                        </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className="text-sm text-slate-300">{user.role}</span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`inline-flex px-3 py-1 text-xs font-semibold rounded-full ${
                                            user.status === 'active'
                                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                                : 'bg-slate-500/10 text-slate-400 border border-slate-500/20'
                                        }`}>
                                            {user.status}
                                        </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right">
                                    <div className="flex items-center justify-end gap-2">
                                        <button
                                            onClick={() => openEditModal(user)}
                                            className="p-2 text-slate-400 hover:text-blue-400 hover:bg-slate-800 rounded-lg transition-colors"
                                            title="Edit user"
                                        >
                                            <Edit2 className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => handleDelete(user.id)}
                                            className="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-colors"
                                            title="Delete user"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                </div>

                {filteredUsers.length === 0 && (
                    <div className="text-center py-12">
                        <Users className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                        <p className="text-slate-400">No users found</p>
                    </div>
                )}
            </div>

            <div className="grid grid-cols-4 gap-4 mt-6">
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                    <div className="text-slate-400 text-sm font-medium mb-1">Total Users</div>
                    <div className="text-2xl font-bold text-white">{users.length}</div>
                </div>
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                    <div className="text-slate-400 text-sm font-medium mb-1">Active Users</div>
                    <div className="text-2xl font-bold text-emerald-400">{users.filter(u => u.status === 'active').length}</div>
                </div>
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                    <div className="text-slate-400 text-sm font-medium mb-1">Teams</div>
                    <div className="text-2xl font-bold text-blue-400">{new Set(users.map(u => u.team)).size}</div>
                </div>
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                    <div className="text-slate-400 text-sm font-medium mb-1">Inactive Users</div>
                    <div className="text-2xl font-bold text-slate-400">{users.filter(u => u.status === 'inactive').length}</div>
                </div>
            </div>

            {showModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-md shadow-2xl">
                        <div className="flex items-center justify-between p-6 border-b border-slate-800">
                            <h2 className="text-xl font-bold text-white">
                                {modalMode === 'create' ? 'Add New User' : 'Edit User'}
                            </h2>
                            <button
                                onClick={() => setShowModal(false)}
                                className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">Name</label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-blue-600"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">Email</label>
                                <input
                                    type="email"
                                    value={formData.email}
                                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                    className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-blue-600"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">Team</label>
                                <select
                                    value={formData.team}
                                    onChange={(e) => setFormData({ ...formData, team: e.target.value })}
                                    className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-blue-600"
                                >
                                    <option value="">Select a team</option>
                                    {teams.map(team => (
                                        <option key={team} value={team}>{team}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">Role</label>
                                <select
                                    value={formData.role}
                                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                                    className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-blue-600"
                                >
                                    <option value="">Select a role</option>
                                    {roles.map(role => (
                                        <option key={role} value={role}>{role}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">Status</label>
                                <select
                                    value={formData.status}
                                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                                    className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-blue-600"
                                >
                                    <option value="active">Active</option>
                                    <option value="inactive">Inactive</option>
                                </select>
                            </div>

                            <div className="flex gap-3 pt-4">
                                <button
                                    onClick={() => setShowModal(false)}
                                    className="flex-1 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg font-medium transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleSave}
                                    className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
                                >
                                    {modalMode === 'create' ? 'Create User' : 'Update User'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default UsersView;