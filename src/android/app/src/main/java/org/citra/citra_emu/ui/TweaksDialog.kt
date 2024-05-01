// Copyright 2024 Citra Enhanced Project
// Licensed under GPLv2 or any later version
// Refer to the license.txt file included.

package org.citra.citra_emu.ui

import android.content.Context
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.CompoundButton
import android.widget.TextView
import androidx.recyclerview.widget.DividerItemDecoration
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.materialswitch.MaterialSwitch
import org.citra.citra_emu.NativeLibrary
import org.citra.citra_emu.R

class TweaksDialog(context: Context) : BaseSheetDialog(context) {

    private lateinit var adapter: SettingsAdapter

    companion object {
        // tweaks
        const val SETTING_RAISE_CPU_TICKS = 0
        const val SETTING_SKIP_SLOW_DRAW = 1
        const val SETTING_SKIP_TEXTURE_COPY = 2
        const val SETTING_PRIORITY_BOOST = 3

        // view type
        const val TYPE_SWITCH = 0
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.dialog_tweaks)

        val recyclerView: RecyclerView = findViewById(R.id.list_settings)
        recyclerView.layoutManager = LinearLayoutManager(context)
        adapter = SettingsAdapter(context)
        recyclerView.adapter = adapter
        recyclerView.addItemDecoration(DividerItemDecoration(context, DividerItemDecoration.VERTICAL))
    }

    override fun onStop() {
        super.onStop()
        adapter.saveSettings()
    }

    inner class SettingsItem(
        private val setting: Int,
        private val name: String,
        private val type: Int,
        private var value: Int
    ) {
        fun getType(): Int {
            return type
        }

        fun getSetting(): Int {
            return setting
        }

        fun getName(): String {
            return name
        }

        fun getValue(): Int {
            return value
        }

        fun setValue(setValue: Int) {
            value = setValue
        }
    }

    abstract class SettingViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView), View.OnClickListener {
        init {
            itemView.setOnClickListener(this)
            findViews(itemView)
        }

        protected abstract fun findViews(root: View)
        abstract fun bind(item: SettingsItem)
        override fun onClick(clicked: View) {
            // handle click event
        }
    }

    inner class SwitchSettingViewHolder(itemView: View) : SettingViewHolder(itemView), CompoundButton.OnCheckedChangeListener {
        private var settingsItem: SettingsItem? = null
        private var textSettingName: TextView? = null
        private var switch: MaterialSwitch? = null

        init {
            findViews(itemView)
        }

        override fun findViews(root: View) {
            textSettingName = root.findViewById(R.id.text_setting_name)
            switch = root.findViewById(R.id.switch_widget)
            switch?.setOnCheckedChangeListener(this)
        }

        override fun bind(item: SettingsItem) {
            settingsItem = item
            textSettingName?.text = item.getName()
            switch?.isChecked = item.getValue() > 0
        }

        override fun onClick(clicked: View) {
            switch?.toggle()
            settingsItem?.setValue(if (switch?.isChecked == true) 1 else 0)
        }

        override fun onCheckedChanged(view: CompoundButton, isChecked: Boolean) {
            settingsItem?.setValue(if (isChecked) 1 else 0)
        }
    }

    inner class SettingsAdapter(context: Context) : RecyclerView.Adapter<SettingViewHolder>() {
        private var tweaks: IntArray
        private var settings: ArrayList<SettingsItem>

        init {
            var i = 0
            tweaks = NativeLibrary.getTweaks()
            settings = ArrayList()

            // native settings
            settings.add(SettingsItem(SETTING_RAISE_CPU_TICKS, context.getString(R.string.raise_cpu_ticks), TYPE_SWITCH, tweaks[i++]))
            settings.add(SettingsItem(SETTING_SKIP_SLOW_DRAW, context.getString(R.string.skip_slow_draw), TYPE_SWITCH, tweaks[i++]))
            settings.add(SettingsItem(SETTING_SKIP_TEXTURE_COPY, context.getString(R.string.skip_texture_copy), TYPE_SWITCH, tweaks[i++]))
            settings.add(SettingsItem(SETTING_PRIORITY_BOOST, context.getString(R.string.priority_boost_tweaks), TYPE_SWITCH, tweaks[i++]))
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): SettingViewHolder {
            val inflater = LayoutInflater.from(parent.context)
            return when (viewType) {
                TYPE_SWITCH -> {
                    val itemView = inflater.inflate(R.layout.list_item_tweaks_switch, parent, false)
                    SwitchSettingViewHolder(itemView)
                }
                else -> throw IllegalArgumentException("Invalid view type")
            }
        }

        override fun getItemCount(): Int {
            return settings.size
        }

        override fun getItemViewType(position: Int): Int {
            return settings[position].getType()
        }

        override fun onBindViewHolder(holder: SettingViewHolder, position: Int) {
            holder.bind(settings[position])
        }

        fun saveSettings() {
            // native settings
            var isChanged = false
            val newSettings = IntArray(tweaks.size)
            for (i in tweaks.indices) {
                newSettings[i] = settings[i].getValue()
                if (newSettings[i] != tweaks[i]) {
                    isChanged = true
                }
            }
            // apply settings if changes are detected
            if (isChanged) {
                NativeLibrary.setTweaks(newSettings)
            }
        }
    }
}
