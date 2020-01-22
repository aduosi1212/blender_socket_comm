# Author: Adnan Munawar
# Email: amunawa2@jh.edu
# Lab: LCSR

bl_info = {
    "name": "Socket Client for Blender",
    "author": "Adnan Munawar",
    "version": (0, 1),
    "blender": (2, 79, 0),
    "location": "View3D > Tool > SocketClient",
    "description": "",
    "warning": "",
    "wiki_url": "https://github.com/adnanmunawar/blender_socket_comm",
    "category": "SocketClient",
}

import bpy
from bpy.props import StringProperty, IntProperty
import socket
from collections import Counter
import time
from data_utils import *

# Globals
server_addr = ''
server_port = 3004
client = None
rx_handle = None

# GRAMMAR
DISCONNECT = ""
SET_VTX_POS = "SET_VTX_POS"
GET_VTX_POS = "GET_VTX_POS"

SET_VTX_POS_VEC_SIZE = 4
GET_VTX_POS_VEC_SIZE = 1


def connect(addr=None, port=None):
    global server_addr, server_port, client
    if addr is not None:
        server_addr = addr
    if port is not None:
        server_port = port

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client.connect((server_addr, server_port))
        client.setblocking(False)
    except socket.error:
        client = None
        pass


def disconnect():
    global client
    print('Disconnect Called')
    if client:
        bpy.app.handlers.scene_update_pre.remove(rx_handle)
        print('Closing Client', client)
        client.close()
        client = None


def set_vtx_pos(obj, idx, x, y, z):
    if obj:
        # print('MOVING VTX(', idx, ') : ', x, y, z)
        num_vtx = len(obj.data.vertices)
        if 0 <= idx < num_vtx:
            obj.data.vertices[idx].co = (x, y, z)
        else:
            print('Error, Vtx Idx Invalid')


def get_vtx_pos(obj, idx):
    global client
    if obj:
        # print('MOVING VTX(', idx, ') : ', x, y, z)
        num_vtx = len(obj.data.vertices)
        if 0 <= idx < num_vtx:
            pos = obj.data.vertices[idx].co
            if client:
                vec = [idx, pos[0], pos[1], pos[2]]
                data = pack_vector(vec)
                packet = GET_VTX_POS + data
                client.send(packet.encode())
        else:
            print('Error, Vtx Idx Invalid')


def client_rx(args):
    try:
        packet = client.recv(1024)
        packet = packet.decode()
        if packet == DISCONNECT:
            disconnect()
        elif packet.find(GET_VTX_POS) == 0:
            data = packet.split(GET_VTX_POS)[1]
            idx = unpack_vector(data, GET_VTX_POS_VEC_SIZE)
            get_vtx_pos(bpy.data.object, idx)
        elif packet.find(SET_VTX_POS):
            data = packet.split(SET_VTX_POS)[1]
            idx, x, y, z = unpack_vector(data, SET_VTX_POS_VEC_SIZE)
            set_vtx_pos(bpy.data.object, idx, x, y, z)
    except socket.error:
        pass


class ConnectOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "scene.socket_connect_operator"
    bl_label = "Connect To Server"

    def execute(self, context):
        global rx_handle
        if client is None:
            connect(context.scene.server_addr, context.scene.server_port)
            bpy.app.handlers.scene_update_pre.append(client_rx)
            rx_handle = client_rx
        return {'FINISHED'}


class DisconnectOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "scene.socket_disconnect_operator"
    bl_label = "Disconnect"

    def execute(self, context):
        disconnect()
        return {'FINISHED'}


class BlenderClientPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Blender Client Panel"
    bl_idname = "Blender_PT_Client"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "SocketClient"

    bpy.types.Scene.server_addr = StringProperty(name="Server Addr", default="localhost", description="Server Addr")
    bpy.types.Scene.server_port = IntProperty(name="Server Port", default=3001, description="Server Port")

    def draw(self, context):
        global client
        layout = self.layout

        row = layout.row()
        row.label(text="Blender Client!", icon='WORLD_DATA')

        row = layout.row()
        row.prop(context.scene, 'server_addr')

        row = layout.row()
        row.prop(context.scene, 'server_port')

        row = layout.row()
        row.enabled = not bool(client)
        row.operator('scene.socket_connect_operator')

        row = layout.row()
        row.enabled = bool(client)
        row.operator('scene.socket_disconnect_operator')


classes = (ConnectOperator, DisconnectOperator, BlenderClientPanel)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
    #ungregister()
