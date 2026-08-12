Component({
  properties: {
    value: {
      type: Number,
      value: 5,
      observer(value) {
        this.syncValue(value);
      },
    },
  },

  data: {
    percent: 50,
  },

  lifetimes: {
    attached() {
      this.syncValue(this.properties.value);
    },
  },

  methods: {
    clamp(value) {
      return Math.max(1, Math.min(10, Math.round(Number(value) || 1)));
    },

    syncValue(value) {
      const nextValue = this.clamp(value);
      this.setData({ percent: Math.round((nextValue / 10) * 100) });
    },

    setFromTouch(event) {
      const touch = event.touches && event.touches[0]
        ? event.touches[0]
        : event.changedTouches && event.changedTouches[0];
      if (!touch) return;

      wx.createSelectorQuery()
        .in(this)
        .select("#intensityTrack")
        .boundingClientRect((rect) => {
          if (!rect || !rect.height) return;
          const y = touch.clientY !== undefined ? touch.clientY : touch.y;
          const ratio = 1 - Math.max(0, Math.min(rect.height, y - rect.top)) / rect.height;
          const value = this.clamp(1 + ratio * 9);
          this.syncValue(value);
          this.triggerEvent("change", { value });
        })
        .exec();
    },

    handleTap(event) {
      this.setFromTouch(event);
    },

    handleTouchMove(event) {
      this.setFromTouch(event);
    },
  },
});
