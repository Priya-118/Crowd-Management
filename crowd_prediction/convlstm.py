"""Encoder-Decoder ConvLSTM for crowd-density map prediction (PyTorch).

Idea (Shi et al., 2015): an LSTM whose gates are convolutions, so the hidden
state stays a spatial map and the model learns *where* crowd mass moves, not
just how much there is.

  encoder : reads t_in past maps, builds a hidden state per layer
  decoder : starts from the encoder state and rolls out t_out future maps,
            feeding each prediction back in (autoregressive)
"""
from __future__ import annotations
import random
import torch
import torch.nn as nn


class ConvLSTMCell(nn.Module):
    def __init__(self, in_ch, hid_ch, k=3):
        super().__init__()
        self.hid = hid_ch
        self.conv = nn.Conv2d(in_ch + hid_ch, 4 * hid_ch, k, padding=k // 2)
        with torch.no_grad():
            self.conv.bias[hid_ch:2 * hid_ch].fill_(1.0)    # forget-gate bias = 1

    def forward(self, x, state):
        h, c = state
        i, f, o, g = torch.chunk(self.conv(torch.cat([x, h], 1)), 4, 1)
        c = torch.sigmoid(f) * c + torch.sigmoid(i) * torch.tanh(g)
        h = torch.sigmoid(o) * torch.tanh(c)
        return h, c

    def zero_state(self, B, H, W, device):
        z = torch.zeros(B, self.hid, H, W, device=device)
        return z, z.clone()


class ConvLSTMEncoderDecoder(nn.Module):
    def __init__(self, in_ch=1, hidden=(32, 32), k=3, residual=True):
        super().__init__()
        chs = [in_ch, *hidden]
        self.enc = nn.ModuleList(ConvLSTMCell(chs[i], chs[i + 1], k) for i in range(len(hidden)))
        self.dec = nn.ModuleList(ConvLSTMCell(chs[i], chs[i + 1], k) for i in range(len(hidden)))
        self.head = nn.Conv2d(hidden[-1], in_ch, 1)
        self.residual = residual        # predict the *change* from the previous map

    def forward(self, x, t_out, target=None, tf_ratio=0.0):
        """x: (B, t_in, C, H, W) -> (B, t_out, C, H, W). Output is not clipped."""
        B, T, C, H, W = x.shape
        states = [c.zero_state(B, H, W, x.device) for c in self.enc]
        for t in range(T):
            inp = x[:, t]
            for l, cell in enumerate(self.enc):
                states[l] = cell(inp, states[l]); inp = states[l][0]
        prev, outs = x[:, -1], []
        for t in range(t_out):
            inp = prev
            for l, cell in enumerate(self.dec):
                states[l] = cell(inp, states[l]); inp = states[l][0]
            y = self.head(inp) + (prev if self.residual else 0)
            outs.append(y)
            use_gt = target is not None and tf_ratio > 0 and random.random() < tf_ratio
            prev = target[:, t] if use_gt else y
        return torch.stack(outs, 1)
